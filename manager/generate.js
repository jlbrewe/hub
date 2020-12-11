/**
 * Script to generate Python files from Javascript dependencies.
 *
 * The generated files should be committed so that Python developers,
 * and deployments don't need to run `npm install` first.
 */

const fs = require("fs");
const path = require("path");

thema();
components();
emailTemplates();

/**
 * Generate `manager/themes.py` with the version of
 * Thema to use and the names of themes available.
 */
function thema() {
  console.log("Generating manager/themes.py");

  const json = fs.readFileSync(
    path.join(
      require.resolve("@stencila/thema"),
      "..",
      "..",
      "..",
      "package.json"
    ),
    "utf8"
  );
  const version = JSON.parse(json).version;

  const themes = require("@stencila/thema").themes;

  fs.writeFileSync(
    path.join(__dirname, "manager", "themes.py"),
    `# Generated by ${path.basename(
      __filename
    )}. Commit this file, but do not edit it.

from manager.helpers import EnumChoice

# The version of Thema to use
version = "${version}"


class Themes(EnumChoice):
    """The list of Thema themes."""

${Object.keys(themes)
  .map(theme => `    ${theme} = "${theme}"`)
  .join("\n")}
`
  );
}

/**
 * Generate `manager/themes.py` with the version of
 * Thema to use and the names of themes available.
 */
function components() {
  console.log("Generating manager/components.py");

  const json = fs.readFileSync(
    path.join(
      require.resolve("@stencila/components"),
      "..",
      "..",
      "package.json"
    ),
    "utf8"
  );
  const version = JSON.parse(json).version;

  fs.writeFileSync(
    path.join(__dirname, "manager", "components.py"),
    `# Generated by ${path.basename(
      __filename
    )}. Commit this file, but do not edit it.

# The version of @stencila/components to use
version = "${version}"
`
  );
}

/**
 * Copy email templates from `@stencila/email-templates` to
 * the Django template directory.
 */
function emailTemplates() {
  console.log("Copying templates to users/templates/account/email");

  const src = path.join(
    "node_modules",
    "@stencila",
    "email-templates",
    "dist",
    "transactional"
  );

  // Email verification on signup (requires some context variable renaming)
  const emailConfirmationSignup = fs
    .readFileSync(path.join(src, "account-confirmation.html"), "utf8")
    .replace(
      "{{ reason_for_contacting }}",
      `This email was sent because someone, most likely you, used this address to signup to Stencila Hub.<br />
       If it was not you, please ignore this email.`
    );
  fs.writeFileSync(
    "users/templates/account/email/email_confirmation_signup_message.html",
    emailConfirmationSignup
  );

  // Email verification at some other time using `me/email/` settings page
  const emailConfirmation = fs
    .readFileSync(path.join(src, "email-confirmation.html"), "utf8")
    .replace(
      "{{ reason_for_contacting }}",
      `This email was sent because someone, most likely you, added this address to their Stencila Hub account.<br />
       If it was not you, please ignore this email.`
    );
  fs.writeFileSync(
    "users/templates/account/email/email_confirmation_message.html",
    emailConfirmation
  );

  // Password reset email
  const passwordReset = fs
    .readFileSync(path.join(src, "password-reset.html"), "utf8")
    .replace(
      "{{ reason_for_contacting }}",
      `This email was sent because someone used this address to reset their password on Stencila Hub.<br />
       If it was not you, please ignore this email.`
    );
  fs.writeFileSync(
    "users/templates/account/email/password_reset_key_message.html",
    passwordReset
  );

  // Invitation email
  fs.copyFileSync(
    path.join(src, "user-invitation.html"),
    "users/templates/invitations/email/email_invite_message.html"
  );
}
