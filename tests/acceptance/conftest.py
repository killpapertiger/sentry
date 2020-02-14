from __future__ import absolute_import, print_function

import os
import json
import subprocess
import time

# note(joshuarli): if i'm correct about .webpack.meta always being written in git root, then this lets you run pytest from anywhere
# also this helps call vendored yarn

def gitroot(start=os.getcwd()):
    gitroot, root = start, "/"
    while not os.path.isdir(os.path.join(gitroot, ".git")):
        gitroot = os.path.abspath(os.path.join(gitroot, os.pardir))
        if gitroot == root:
            raise RuntimeError("failed to locate a git root directory")
    return gitroot


def pytest_configure(config):
    """
    Generate frontend assets before running any acceptance tests

    TODO: There is a bug if you run `py.test` with `-f` -- the built
    assets will trigger another `py.test` run.
    """

    # Do not build in CI because tests are run w/ `make test-acceptance` which builds assets
    # Can also skip with the env var `SKIP_ACCEPTANCE_UI_BUILD`
    # `CI` is a default env var on Travis CI (see: https://docs.travis-ci.com/user/environment-variables/#default-environment-variables)
    if os.environ.get("CI") or os.environ.get("SKIP_ACCEPTANCE_UI_BUILD"):
        return

    fp = os.path.join(gitroot(), ".webpack.meta")

    try:
        with open(fp) as f:
            data = json.load(f)

            # If built within last hour, do not build again
            last_built = int(time.time()) - data["built"]

            if last_built <= 3600:
                print(  # noqa: B314
                    u"""
###################
#
# Frontend assets last built {} seconds ago, skipping rebuilds for another {} seconds.
# Delete the file: `{}` to rebuild.
#
###################
                """.format(
                        last_built, 3600 - last_built, fp
                    )
                )
                return
    except IOError:
        pass
    except Exception:
        pass

    print(  # noqa: B314
        """
###################
#
# Running webpack to compile frontend assets - this will take awhile
#
###################
    """
    )

    subprocess.call(
        [os.path.join(fp, "bin", "yarn"), "webpack"],
        env={
            "NODE_ENV": "development",
            "PATH": os.environ["PATH"],
            "NODE_OPTIONS": "--max-old-space-size=4096",
        },
    )
