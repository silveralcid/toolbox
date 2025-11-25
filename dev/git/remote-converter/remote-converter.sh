#!/usr/bin/env bash

# ============================================
# Git Remote Conversion Tool (Linux/macOS)
# Modes:
#   1 = Convert all to HTTPS
#   2 = Convert all to SSH
#   3 = Flip each (HTTPS <-> SSH)
# ============================================

ROOT_DIR="$HOME/dev"   # <-- change this to your root folder
LOG_FILE="$(pwd)/repo-remote-tool.log"

echo "=== Git Remote Tool Log $(date) ===" > "$LOG_FILE"
echo

echo "Select mode:"
echo "1. Convert ALL to HTTPS"
echo "2. Convert ALL to SSH"
echo "3. Flip each (HTTPS <-> SSH)"
read -p "Enter mode number: " MODE

if [[ "$MODE" != "1" && "$MODE" != "2" && "$MODE" != "3" ]]; then
    echo "Invalid mode. Exiting."
    exit 1
fi

# Iterate over directories inside ROOT_DIR
for repo in "$ROOT_DIR"/*; do

    # Must be a directory with a .git folder
    if [[ ! -d "$repo/.git" ]]; then
        continue
    fi

    echo
    echo "Checking repo: $repo"
    echo "Repo: $repo" >> "$LOG_FILE"

    # Get remote origin URL
    REMOTE=$(git -C "$repo" remote get-url origin 2>/dev/null)

    if [[ -z "$REMOTE" ]]; then
        echo "  No origin remote."
        echo "  No origin remote." >> "$LOG_FILE"
        continue
    fi

    echo "  Current: $REMOTE" >> "$LOG_FILE"

    IS_HTTPS=$(echo "$REMOTE" | grep -E "^https://github.com/")
    IS_SSH=$(echo "$REMOTE" | grep -E "^git@github.com:")

    case "$MODE" in

        # ============================================
        # MODE 1 — Convert all to HTTPS
        # ============================================
        1)
            if [[ "$IS_HTTPS" ]]; then
                echo "  Already HTTPS."
                echo "  Already HTTPS." >> "$LOG_FILE"
                continue
            fi

            if [[ "$IS_SSH" ]]; then
                CLEAN=$(echo "$REMOTE" | sed -E 's|^git@github.com:||; s|\.git/?$||')
                NEW="https://github.com/$CLEAN.git"

                echo "  SSH → HTTPS: $NEW"
                echo "  SSH → HTTPS: $NEW" >> "$LOG_FILE"

                git -C "$repo" remote set-url origin "$NEW"
                continue
            fi

            echo "  Unsupported remote format."
            echo "  Unsupported format." >> "$LOG_FILE"
            ;;

        # ============================================
        # MODE 2 — Convert all to SSH
        # ============================================
        2)
            if [[ "$IS_SSH" ]]; then
                echo "  Already SSH."
                echo "  Already SSH." >> "$LOG_FILE"
                continue
            fi

            if [[ "$IS_HTTPS" ]]; then
                CLEAN=$(echo "$REMOTE" | sed -E 's|^https://github.com/||; s|\.git/?$||')
                NEW="git@github.com:$CLEAN.git"

                echo "  HTTPS → SSH: $NEW"
                echo "  HTTPS → SSH: $NEW" >> "$LOG_FILE"

                git -C "$repo" remote set-url origin "$NEW"
                continue
            fi

            echo "  Unsupported remote format."
            echo "  Unsupported format." >> "$LOG_FILE"
            ;;

        # ============================================
        # MODE 3 — Flip each
        # ============================================
        3)
            if [[ "$IS_HTTPS" ]]; then
                CLEAN=$(echo "$REMOTE" | sed -E 's|^https://github.com/||; s|\.git/?$||')
                NEW="git@github.com:$CLEAN.git"

                echo "  FLIP: HTTPS → SSH: $NEW"
                echo "  FLIP: HTTPS → SSH: $NEW" >> "$LOG_FILE"

                git -C "$repo" remote set-url origin "$NEW"
                continue
            fi

            if [[ "$IS_SSH" ]]; then
                CLEAN=$(echo "$REMOTE" | sed -E 's|^git@github.com:||; s|\.git/?$||')
                NEW="https://github.com/$CLEAN.git"

                echo "  FLIP: SSH → HTTPS: $NEW"
                echo "  FLIP: SSH → HTTPS: $NEW" >> "$LOG_FILE"

                git -C "$repo" remote set-url origin "$NEW"
                continue
            fi

            echo "  Unsupported remote format."
            echo "  Unsupported format." >> "$LOG_FILE"
            ;;
    esac

done

echo
echo "Done. Log saved to: $LOG_FILE"
