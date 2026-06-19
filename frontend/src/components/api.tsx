import wretch from "wretch"

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"

export const api = wretch(API_BASE_URL)
  .options({ credentials: "include" })
