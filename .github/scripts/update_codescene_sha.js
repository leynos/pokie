// Keep workflow logic in source so code scanners can inspect it.
module.exports = async ({ github, context }) => {
  await github.rest.actions.updateRepoVariable({
    owner: context.repo.owner,
    repo: context.repo.repo,
    name: 'CODESCENE_CLI_SHA256',
    value: process.env.SHA,
  });
};
