// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";

export interface AppShellProps {
  children: ReactNode;
}

/** Top-level layout — header, content area, footer. */
export function AppShell({ children }: AppShellProps) {
  const location = useLocation();
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex max-w-5xl items-center justify-between p-4">
          <Link to="/" className="text-lg font-semibold">
            AgentForge
          </Link>
          <nav className="flex gap-4 text-sm">
            <Link
              to="/agents"
              className={
                location.pathname.startsWith("/agents")
                  ? "text-accent"
                  : "text-muted hover:text-fg"
              }
            >
              Agents
            </Link>
            <Link
              to="/demo"
              className={
                location.pathname === "/demo"
                  ? "text-accent"
                  : "text-muted hover:text-fg"
              }
            >
              Demo
            </Link>
            <Link
              to="/login"
              className={
                location.pathname === "/login"
                  ? "text-accent"
                  : "text-muted hover:text-fg"
              }
            >
              Sign in
            </Link>
          </nav>
        </div>
      </header>

      <main className="flex-1">{children}</main>

      <footer className="border-t border-border bg-surface">
        <div className="mx-auto max-w-5xl p-4 text-xs text-muted">
          AgentForge — Phase 1. The CLI is unchanged.
        </div>
      </footer>
    </div>
  );
}
