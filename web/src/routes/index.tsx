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

import { Link } from "react-router-dom";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";

/** Landing page. */
export function IndexPage() {
  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-8 p-8">
      <header className="space-y-2">
        <h1 className="text-4xl font-semibold tracking-tight">AgentForge</h1>
        <p className="text-muted">
          AI Agent Development, Evaluation &amp; Deployment Platform.
        </p>
      </header>

      <Card title="Try the demo" subtitle="No API key required.">
        <p className="text-sm text-muted">
          Walk through a pre-seeded project: two agents, a workflow, an
          evaluation dataset, and a populated trace dashboard. Phase 1
          returns a placeholder; full content arrives in Phase 14.
        </p>
        <div className="mt-4 flex gap-3">
          <Link to="/demo">
            <Button>Try Demo</Button>
          </Link>
          <Link to="/login">
            <Button variant="ghost">Sign in</Button>
          </Link>
        </div>
      </Card>

      <Card title="What this is">
        <p className="text-sm text-muted">
          AgentForge is the web frontend for the{" "}
          <code className="rounded bg-surface px-1 py-0.5 font-mono text-xs">
            agents-cli
          </code>{" "}
          foundation. The CLI is unchanged. This app wraps the same eval
          flywheel, deploy targets, and ADK-backed agent runtime in a
          browser experience.
        </p>
      </Card>
    </div>
  );
}
