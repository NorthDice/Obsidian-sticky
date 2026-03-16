#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"

cat > "$HOME/.local/share/applications/obsidian-sticky.desktop" <<EOF
[Desktop Entry]
Name=Obsidian Sticky
Comment=Sticky notes from Obsidian vault
Exec=$DIR/start.sh
Path=$DIR
Icon=$DIR/icon.svg
Type=Application
Categories=Utility;
StartupNotify=false
EOF

cp "$HOME/.local/share/applications/obsidian-sticky.desktop" "$HOME/Desktop/" 2>/dev/null

echo "Installed! Shortcut added to app menu and desktop."
