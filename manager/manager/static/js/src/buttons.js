// Improve feedback UX for async interactions with HTMX buttons by showing a spinner on user click.
const findHTMXButtons = () =>
  document.querySelectorAll(`
    .button[hx-delete],
    .button[hx-get],
    .button[hx-patch],
    .button[hx-post],
    .button[hx-put],
    form[hx-delete] .button[type="submit"],
    form[hx-get] .button[type="submit"],
    form[hx-patch] .button[type="submit"],
    form[hx-post] .button[type="submit"],
    form[hx-put] .button[type="submit"],
    form[action] button[type="submit"]
`);

const attachClickHandler = (button) => {
  button.addEventListener("click", () => {
    button.classList.add("is-loading");
  });
};

export const enrichHTMXButtons = () => {
  findHTMXButtons().forEach(attachClickHandler);

  // Remove `loading` state from buttons after a request has been completed.
  htmx.on("htmx:afterRequest", (e) => {
    if (e.target instanceof HTMLButtonElement) {
      e.target.classList.remove("is-loading");
    } else if (e.target instanceof HTMLFormElement) {
      const button = document.querySelector("button.is-loading")
      if (button) button.classList.remove("is-loading");
    }
  });
};