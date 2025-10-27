package utils

import (
	"bufio"
	"context"
	"encoding/json"
	"log"
	"os"
	"path/filepath"

	sitter "github.com/smacker/go-tree-sitter"
	"github.com/smacker/go-tree-sitter/java"
	"github.com/smacker/go-tree-sitter/python"
)

func ProcessFile(path string, out *bufio.Writer) {
	src, err := os.ReadFile(path)
	if err != nil {
		return
	}

	var lang *sitter.Language
	switch filepath.Ext(path) {
	case ".py":
		lang = python.GetLanguage()
	case ".java":
		lang = java.GetLanguage()
	default:
		return
	}

	parser := sitter.NewParser()
	parser.SetLanguage(lang)
	tree, err := parser.ParseCtx(context.Background(), nil, src) // nil oldTree
	if err != nil || tree == nil {
		return
	}
	root := tree.RootNode()
	extractAndEmit(path, lang, src, root, out)
}

func extractAndEmit(path string, lang *sitter.Language, src []byte, node *sitter.Node, out *bufio.Writer) {
	for i := 0; i < int(node.ChildCount()); i++ {
		child := node.Child(i)
		if child == nil {
			continue
		}

		switch child.Type() {
		case "function_definition", "method_declaration", "class_definition", "class_declaration", "constructor_declaration":
			text := string(src[child.StartByte():child.EndByte()])

			item := OutputChunk{
				Path:      path,
				Language:  detectLanguage(lang),
				Code:      text,
				StartLine: int(child.StartPoint().Row) + 1,
				EndLine:   int(child.EndPoint().Row) + 1,
			}

			j, _ := json.Marshal(item)
			if _, err := out.WriteString(string(j) + "\n"); err != nil {
				log.Printf("Failed to write output for %s: %v", path, err)
				return
			}
		}

		extractAndEmit(path, lang, src, child, out)
	}
}

func detectLanguage(lang *sitter.Language) string {
	switch lang {
	case python.GetLanguage():
		return "python"
	case java.GetLanguage():
		return "java"
	default:
		return "unknown"
	}
}
