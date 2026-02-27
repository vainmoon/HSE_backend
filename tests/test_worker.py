import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from errors import ItemNotFoundError
from models.items import ItemModel
from models.moderation_results import ModerationResultModel
from models.sellers import SellerModel
from workers.moderation_worker import handle_message, process_message

MESSAGE = {
    'task_id': 1,
    'item_id': 2,
    'timestamp': '2026-02-27T00:00:00+00:00',
    'retry_count': 0,
}


def _make_item() -> ItemModel:
    return ItemModel(id=2, name='Test', description='Desc', category=1, images_qty=3, seller_id=10)


def _make_seller() -> SellerModel:
    return SellerModel(id=10, is_verified_seller=True)


def _make_result(status: str = 'completed') -> ModerationResultModel:
    return ModerationResultModel(
        id=1, item_id=2, status=status,
        is_violation=False, probability=0.1,
        error_message=None,
        created_at=datetime.now(timezone.utc),
        processed_at=None,
    )


@pytest.fixture
def repos():
    item_repo = AsyncMock()
    item_repo.get.return_value = _make_item()

    seller_repo = AsyncMock()
    seller_repo.get.return_value = _make_seller()

    result_repo = AsyncMock()
    result_repo.update_completed.return_value = _make_result()
    result_repo.update_failed.return_value = _make_result(status='failed')

    return item_repo, seller_repo, result_repo


@pytest.fixture
def kafka_client():
    return AsyncMock()


class TestProcessMessage:
    @pytest.mark.asyncio
    async def test_success(self, repos):
        item_repo, seller_repo, result_repo = repos
        model = MagicMock()

        with patch('workers.moderation_worker.predict', return_value=(True, 0.9)):
            await process_message(MESSAGE, model, item_repo, seller_repo, result_repo)

        result_repo.update_completed.assert_awaited_once_with(1, True, 0.9)

    @pytest.mark.asyncio
    async def test_item_not_found_raises(self, repos):
        item_repo, seller_repo, result_repo = repos
        item_repo.get.side_effect = ItemNotFoundError()
        model = MagicMock()

        with pytest.raises(ItemNotFoundError):
            await process_message(MESSAGE, model, item_repo, seller_repo, result_repo)

        result_repo.update_completed.assert_not_awaited()


class TestHandleMessageRetry:
    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self, repos, kafka_client):
        item_repo, seller_repo, result_repo = repos
        model = MagicMock()

        with patch('workers.moderation_worker.process_message', new=AsyncMock()):
            with patch('workers.moderation_worker.MAX_RETRIES', 3):
                await handle_message(MESSAGE, model, kafka_client, item_repo, seller_repo, result_repo)

        kafka_client.send_to_dlq.assert_not_awaited()
        result_repo.update_failed.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_success_on_second_attempt(self, repos, kafka_client):
        item_repo, seller_repo, result_repo = repos
        model = MagicMock()
        mock_process = AsyncMock(side_effect=[Exception('transient'), None])

        with patch('workers.moderation_worker.process_message', new=mock_process):
            with patch('workers.moderation_worker.MAX_RETRIES', 3):
                with patch('asyncio.sleep', new=AsyncMock()):
                    await handle_message(MESSAGE, model, kafka_client, item_repo, seller_repo, result_repo)

        assert mock_process.await_count == 2
        kafka_client.send_to_dlq.assert_not_awaited()
        result_repo.update_failed.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_all_retries_exhausted_sends_to_dlq(self, repos, kafka_client):
        item_repo, seller_repo, result_repo = repos
        model = MagicMock()
        mock_process = AsyncMock(side_effect=Exception('persistent error'))

        with patch('workers.moderation_worker.process_message', new=mock_process):
            with patch('workers.moderation_worker.MAX_RETRIES', 3):
                with patch('asyncio.sleep', new=AsyncMock()):
                    await handle_message(MESSAGE, model, kafka_client, item_repo, seller_repo, result_repo)

        assert mock_process.await_count == 3
        result_repo.update_failed.assert_awaited_once_with(1, 'persistent error')
        kafka_client.send_to_dlq.assert_awaited_once()

        dlq_args = kafka_client.send_to_dlq.await_args.args
        assert dlq_args[1] == 'persistent error'
        assert dlq_args[2] == 3  # retry_count = 0 (from message) + MAX_RETRIES(3)

    @pytest.mark.asyncio
    async def test_retry_count_accumulates_in_dlq(self, repos, kafka_client):
        item_repo, seller_repo, result_repo = repos
        model = MagicMock()
        message_with_retries = {**MESSAGE, 'retry_count': 3}
        mock_process = AsyncMock(side_effect=Exception('error'))

        with patch('workers.moderation_worker.process_message', new=mock_process):
            with patch('workers.moderation_worker.MAX_RETRIES', 3):
                with patch('asyncio.sleep', new=AsyncMock()):
                    await handle_message(
                        message_with_retries, model, kafka_client,
                        item_repo, seller_repo, result_repo,
                    )

        dlq_args = kafka_client.send_to_dlq.await_args.args
        assert dlq_args[2] == 6  # 3 (initial) + 3 (MAX_RETRIES)
