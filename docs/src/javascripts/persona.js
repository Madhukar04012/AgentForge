/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

// Event delegation — works with Material's instant navigation
document.addEventListener("click", function (e) {
  var btn = e.target.closest(".segmented-toggle-inner span");
  if (!btn) return;
  var persona = btn.getAttribute("data-persona");
  document.querySelectorAll(".persona-panel").forEach(function (p) {
    p.classList.remove("active");
  });
  document.querySelectorAll(".segmented-toggle-inner span").forEach(function (b) {
    b.classList.remove("active");
  });
  document.getElementById("panel-" + persona).classList.add("active");
  btn.classList.add("active");
});

// Make GitHub repo link open in a new tab
document.addEventListener("DOMContentLoaded", function() {
  function setRepoLinkTarget() {
    var repoLink = document.querySelector('a[href*="github.com"]');
    if (repoLink) {
      repoLink.setAttribute("target", "_blank");
      repoLink.setAttribute("rel", "noopener noreferrer");
    }
  }

  setRepoLinkTarget();

  // Re-apply on instant navigation (Material theme feature)
  document$.subscribe(function() {
    setRepoLinkTarget();
  });
});
