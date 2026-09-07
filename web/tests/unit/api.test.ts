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
import { ApiError, apiGet, apiPost } from "../../src/lib/api";

const fetchMock = vi.fn();

afterEach(() => {
  fetchMock.mockReset();
});

describe("apiGet / apiPost", () => {
  it("sends credentials and JSON headers", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify([{ id: "1" }]), { status: 200 }),
    );
    // @ts-expect-error - test stub
    globalThis.fetch = fetchMock;

    await apiGet<unknown[]>("/api/v1/agents");

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/agents");
    expect(init.method).toBe("GET");
    expect(init.credentials).toBe("include");
    expect((init.headers as Record<string, string>)["Content-Type"]).toBe(
      "application/json",
    );
  });

  it("serializes the body and returns parsed JSON on 2xx", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ id: "abc" }), { status: 201 }),
    );
    // @ts-expect-error - test stub
    globalThis.fetch = fetchMock;

    const result = await apiPost<{ id: string }, { name: string }>(
      "/api/v1/agents",
      { name: "x" },
    );

    expect(result).toEqual({ id: "abc" });
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(init.body).toBe(JSON.stringify({ name: "x" }));
    expect(init.method).toBe("POST");
  });

  it("throws an ApiError on non-2xx with the server's detail", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "nope" }), { status: 404 }),
    );
    // @ts-expect-error - test stub
    globalThis.fetch = fetchMock;

    await expect(apiGet("/api/v1/agents/abc")).rejects.toMatchObject({
      name: "ApiError",
      status: 404,
      message: "nope",
    });
  });

  it("falls back to a synthesized message when the body has no detail", async () => {
    fetchMock.mockResolvedValueOnce(new Response("garbage", { status: 500 }));
    // @ts-expect-error - test stub
    globalThis.fetch = fetchMock;

    try {
      await apiGet("/api/v1/x");
      expect.fail("should have thrown");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      const apiErr = err as ApiError;
      expect(apiErr.status).toBe(500);
      expect(apiErr.message).toMatch(/GET \/api\/v1\/x failed/);
    }
  });
});
