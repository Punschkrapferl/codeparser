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

	numWorkers := runtime.NumCPU()
	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for path := range fileCh {
				utils.ProcessFile(path, out) // call the utility function
			}
		}()
	}

	// Walk directory and send files to channel
	err := filepath.WalkDir(repoDir, func(path string, d fs.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return nil
		}
		ext := filepath.Ext(path)
		if ext == ".py" || ext == ".java" {
			fileCh <- path
		}
		return nil
	})
	if err != nil {
		log.Fatal(err)
	}

	close(fileCh)
	wg.Wait()
}
