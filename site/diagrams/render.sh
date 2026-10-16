#!/usr/bin/env bash
# Randează diagramele PlantUML (*.puml) în ../assets/diagrams/*.svg
# Cerințe: Java 17+. Layout-ul folosește motorul ELK inclus în PlantUML (nu e nevoie de Graphviz).
set -euo pipefail
cd "$(dirname "$0")"

VERSION="1.2026.8"
JAR=".bin/plantuml-${VERSION}.jar"
if [ ! -f "$JAR" ]; then
  mkdir -p .bin
  curl -fsSL -o "$JAR" "https://github.com/plantuml/plantuml/releases/download/v${VERSION}/plantuml-${VERSION}.jar"
fi

mkdir -p ../assets/diagrams
java -jar "$JAR" -tsvg -o ../assets/diagrams ./*.puml
echo "OK: $(ls ../assets/diagrams/*.svg | wc -l) diagrame în site/assets/diagrams/"
