# Independent awk implementation of the validate-user-records job.
#
# This is a user-facing alternative, not the oracle. It exists so that the
# expected outcomes face a second implementation in a different language.
# POSIX awk is weaker than the proposed `int` adapter, which inherits Python's
# `int(text, 10)`, so identifiers are validated with an explicit ASCII
# regular expression; the case `python-int-spellings` declares the resulting
# divergence.
#
# Only POSIX features are used, because CI's `awk` is mawk rather than GNU Awk.
{
    if (match($0, /user=[A-Za-z_][A-Za-z0-9_]* uid=[^ ]+/)) {
        pair = substr($0, RSTART, RLENGTH)
        name = pair
        sub(/^user=/, "", name)
        sub(/ uid=.*$/, "", name)
        raw = pair
        sub(/^user=[^ ]* uid=/, "", raw)
        # The obvious regressive test `raw ~ /^[0-9]+$/` would accept nothing
        # signed, so signs are listed explicitly and the sign is then applied.
        if (raw ~ /^[+-]?[0-9]+$/) {
            value = raw + 0
            if (value >= 0) {
                users[value] = name
                next
            }
        }
        rejected[raw]++
    }
}
END {
    accepted = 0
    for (value in users) {
        accepted++
    }
    total = 0
    for (raw in rejected) {
        total += rejected[raw]
    }
    print accepted, total
}
