package main

import (
	"context"
	"log"
	"os"
	"path/filepath"

	sitter "github.com/smacker/go-tree-sitter"
	"github.com/smacker/go-tree-sitter/java"
	"github.com/smacker/go-tree-sitter/python"
)

var (
	pythonLang = python.GetLanguage()
	javaLang   = java.GetLanguage()
)

func ProcessFile(path string) []OutputChunk {
	var chunks []OutputChunk

	src, err := os.ReadFile(path)
	if err != nil {
		log.Printf("Failed to read %s: %v", path, err)
		return chunks
	}

	var lang *sitter.Language
	switch filepath.Ext(path) {
	case ".py":
		lang = pythonLang
	case ".java":
		lang = javaLang
	default:
		return chunks
	}

	parser := sitter.NewParser()
	parser.SetLanguage(lang)

	tree, err := parser.ParseCtx(context.Background(), nil, src)
	if err != nil || tree == nil {
		return chunks
	}

	extractChunks(path, lang, src, tree.RootNode(), &chunks)
	return chunks
}

func extractChunks(path string, lang *sitter.Language, src []byte, node *sitter.Node, chunks *[]OutputChunk) {
	if node == nil {
		return
	}

	for i := 0; i < int(node.ChildCount()); i++ {
		child := node.Child(i)
		if child == nil {
			continue
		}

		switch child.Type() {
		case "function_definition", "method_declaration", "class_definition", "class_declaration", "constructor_declaration":
			*chunks = append(*chunks, OutputChunk{
				Path:      path,
				Language:  detectLanguage(lang),
				Code:      string(src[child.StartByte():child.EndByte()]),
				StartLine: int(child.StartPoint().Row) + 1,
				EndLine:   int(child.EndPoint().Row) + 1,
			})
		}

		extractChunks(path, lang, src, child, chunks)
	}
}

func detectLanguage(lang *sitter.Language) string {
	switch lang {
	case pythonLang:
		return "python"
	case javaLang:
		return "java"
	default:
		return "unknown"
	}
}
