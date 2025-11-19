package main

import (
	"encoding/json"
	"log"
	"os"
	"path/filepath"
)

func main() {
	if len(os.Args) < 2 {
		log.Fatal("Usage: parser_go run parser_go/main.parser_go <repo-dir>")
	}
	repoDir := os.Args[1]

	var allChunks []OutputChunk

	err := filepath.Walk(repoDir, func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() {
			return err
		}
		ext := filepath.Ext(path)
		if ext != ".py" && ext != ".java" {
			return nil
		}
		chunks := ProcessFile(path)
		allChunks = append(allChunks, chunks...)
		return nil
	})
	if err != nil {
		log.Fatalf("walk failed: %v", err)
	}

	// Ensure api directory exists relative to repo root (../api from project root run)
	outDir := filepath.Join("api")
	if _, err := os.Stat(outDir); os.IsNotExist(err) {
		// try ../api when cwd is project root/parser_go
		outDir = filepath.Join("..", "api")
		_ = os.MkdirAll(outDir, 0o755)
	} else {
		_ = os.MkdirAll(outDir, 0o755)
	}

	// JSONL
	jsonlPath := filepath.Join(outDir, "output.jsonl")
	jsonlFile, err := os.Create(jsonlPath)
	if err != nil {
		log.Fatalf("create jsonl failed: %v", err)
	}
	enc := json.NewEncoder(jsonlFile)
	for _, ch := range allChunks {
		if err := enc.Encode(ch); err != nil {
			log.Fatalf("write jsonl failed: %v", err)
		}
	}
	_ = jsonlFile.Close()

	// JSON array
	jsonPath := filepath.Join(outDir, "output.json")
	arrFile, err := os.Create(jsonPath)
	if err != nil {
		log.Fatalf("create json failed: %v", err)
	}
	if err := json.NewEncoder(arrFile).Encode(allChunks); err != nil {
		log.Fatalf("write json failed: %v", err)
	}
	_ = arrFile.Close()

	log.Printf("Parsed %d chunks. Wrote %s and %s", len(allChunks), jsonlPath, jsonPath)
}
