package main

import (
	"bufio"
	"io/fs"
	"log"
	"os"
	"path/filepath"
	"runtime"
	"sync"

	"codeparser/utils"
)

// Directories to skip entirely
var skipDirs = map[string]struct{}{
	".git":         {},
	"vendor":       {},
	"node_modules": {},
	"build":        {},
	"dist":         {},
	".idea":        {},
	".vscode":      {},
}

func main() {
	if len(os.Args) < 2 {
		log.Fatalf("Usage: %s <repo-directory>", os.Args[0])
	}
	repoDir := os.Args[1]

	out := bufio.NewWriter(os.Stdout)
	defer func() {
		if err := out.Flush(); err != nil {
			log.Fatalf("Failed to flush output: %v", err)
		}
	}()

	fileCh := make(chan string, 100)
	var wg sync.WaitGroup

	// Start worker goroutines
	numWorkers := runtime.NumCPU()
	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for path := range fileCh {
				utils.ProcessFile(path, out)
			}
		}()
	}

	// Walk directory and send relevant files to channel
	err := filepath.WalkDir(repoDir, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return nil // skip files with errors
		}

		if d.IsDir() {
			if _, skip := skipDirs[d.Name()]; skip {
				return fs.SkipDir // skip entire directory
			}
			return nil
		}

		// Only parse Python and Java files
		ext := filepath.Ext(path)
		if ext != ".py" && ext != ".java" {
			return nil
		}

		// Optionally skip very large files (>5MB)
		info, err := d.Info()
		if err == nil && info.Size() > 5*1024*1024 {
			return nil
		}

		fileCh <- path
		return nil
	})
	if err != nil {
		log.Fatal(err)
	}

	close(fileCh)
	wg.Wait()
}
