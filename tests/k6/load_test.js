import http from 'k6/http';
import { sleep, check } from 'k6';

const BASE_URL = 'http://localhost:8000/moderation';

export const options = {
  stages: [
    { duration: '30s', target: 10 },
    { duration: '1m', target: 10 },
    { duration: '30s', target: 0 },
  ],
};

const headers = { 'Content-Type': 'application/json' };

export default function () {
  const predictRes = http.post(`${BASE_URL}/predict`, JSON.stringify({
    seller_id: Math.floor(Math.random() * 1000),
    is_verified_seller: Math.random() > 0.5,
    item_id: Math.floor(Math.random() * 10000),
    name: "Test Item",
    description: "This is a test item for load testing",
    category: Math.floor(Math.random() * 10),
    images_qty: Math.floor(Math.random() * 5),
  }), { headers });

  check(predictRes, {
    'predict status 200': (r) => r.status === 200,
  });

  const itemId = Math.random() > 0.5 ? 3 : 4;

  const simpleRes = http.post(`${BASE_URL}/simple_predict`, JSON.stringify({
    item_id: itemId,
  }), { headers });

  check(simpleRes, {
    'simple_predict status 200': (r) => r.status === 200,
  });

  sleep(1);
}