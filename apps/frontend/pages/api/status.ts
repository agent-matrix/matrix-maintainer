import type { NextApiRequest, NextApiResponse } from "next";

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const backendUrl = process.env.BACKEND_STATUS_URL || "http://127.0.0.1:8000/status";
  const response = await fetch(backendUrl);
  const data = await response.json();
  res.status(200).json(data);
}
