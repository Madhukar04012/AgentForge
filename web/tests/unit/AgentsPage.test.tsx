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

import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { AgentsPage } from "../../src/routes/agents";

const fetchMock = vi.fn();

afterEach(() => {
  fetchMock.mockReset();
});

describe("AgentsPage", () => {
  it("renders an empty state when the API returns []", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify([]), { status: 200 }),
    );
    // @ts-expect-error - test stub
    globalThis.fetch = fetchMock;

    render(
      <MemoryRouter>
        <AgentsPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText(/No agents yet/i)).toBeInTheDocument();
    });
  });

  it("renders one card per agent returned by the API", async () => {
    const agents = [
      {
        id: "a1",
        workspace_id: "w1",
        name: "Compressor",
        description: null,
        current_version_id: "v1",
        created_at: "2026-09-07T00:00:00Z",
        updated_at: "2026-09-07T00:00:00Z",
      },
    ];
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify(agents), { status: 200 }),
    );
    // @ts-expect-error - test stub
    globalThis.fetch = fetchMock;

    render(
      <MemoryRouter>
        <AgentsPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Compressor")).toBeInTheDocument();
    });
  });

  it("shows an error card when the request fails", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "boom" }), { status: 500 }),
    );
    // @ts-expect-error - test stub
    globalThis.fetch = fetchMock;

    render(
      <MemoryRouter>
        <AgentsPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("boom");
    });
  });
});
