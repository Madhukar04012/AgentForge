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

import { Route, Routes } from "react-router-dom";

import { AppShell } from "./components/layout/AppShell";
import { AgentsPage } from "./routes/agents";
import { NewAgentPage } from "./routes/agents.new";
import { AgentDetailPage } from "./routes/agents.id";
import { RunAgentPage } from "./routes/agents.id.run";
import { ExecutionDetailPage } from "./routes/executions.id";
import { IndexPage } from "./routes/index";
import { LoginPage } from "./routes/login";
import { DemoPage } from "./routes/demo";

/** Root component. Defines the route table. */
export function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<IndexPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/demo" element={<DemoPage />} />
        <Route path="/agents" element={<AgentsPage />} />
        <Route path="/agents/new" element={<NewAgentPage />} />
        <Route path="/agents/:id" element={<AgentDetailPage />} />
        <Route path="/agents/:id/run" element={<RunAgentPage />} />
        <Route path="/executions/:id" element={<ExecutionDetailPage />} />
        <Route
          path="*"
          element={
            <div className="p-8 text-center text-muted">
              Page not found.
            </div>
          }
        />
      </Routes>
    </AppShell>
  );
}
