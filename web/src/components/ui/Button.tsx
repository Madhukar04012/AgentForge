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

import { forwardRef, type ButtonHTMLAttributes } from "react";

type Variant = "primary" | "ghost" | "danger";

const VARIANTS: Record<Variant, string> = {
  primary:
    "bg-accent text-white hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed",
  ghost:
    "bg-transparent text-fg hover:bg-surface disabled:opacity-50 disabled:cursor-not-allowed",
  danger:
    "bg-danger text-white hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed",
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

/** A simple, accessible button. */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  function Button({ variant = "primary", className, type, ...rest }, ref) {
    const classes = [
      "inline-flex items-center justify-center rounded-md px-3 py-1.5 text-sm font-medium transition",
      VARIANTS[variant],
      className ?? "",
    ].join(" ");
    return <button ref={ref} type={type ?? "button"} className={classes} {...rest} />;
  },
);
