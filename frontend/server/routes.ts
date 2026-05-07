import type { Express } from "express";
import type { Server } from "http";

// This frontend app has no backend routes — all data comes from the
// microservices backend at api.localhost via the Traefik gateway.
export async function registerRoutes(app: Express, server: Server) {
  // no-op — pure frontend
}
