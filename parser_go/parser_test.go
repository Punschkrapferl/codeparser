package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

// Helper to write a temporary file
func writeTempFile(t *testing.T, ext string, content string) string {
	t.Helper()
	dir := t.TempDir()
	path := filepath.Join(dir, "test"+ext)
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatalf("failed to write temp file: %v", err)
	}
	return path
}

// Helper to check JSON roundtrip
func checkJSONRoundtrip(t *testing.T, chunk OutputChunk) {
	data, err := json.Marshal(chunk)
	if err != nil {
		t.Fatalf("marshal error: %v", err)
	}
	var decoded OutputChunk
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("unmarshal error: %v", err)
	}

	if decoded.Path != chunk.Path {
		t.Errorf("path mismatch: %v vs %v", decoded.Path, chunk.Path)
	}
	if decoded.Language != chunk.Language {
		t.Errorf("language mismatch: %v vs %v", decoded.Language, chunk.Language)
	}
	if decoded.Code != chunk.Code {
		t.Errorf("code mismatch")
	}
	if decoded.StartLine != chunk.StartLine || decoded.EndLine != chunk.EndLine {
		t.Errorf("line numbers mismatch: %v-%v vs %v-%v",
			decoded.StartLine, decoded.EndLine, chunk.StartLine, chunk.EndLine)
	}
}

func TestProcessFileAndJSONRoundtrip(t *testing.T) {
	tests := []struct {
		ext  string
		code string
	}{
		{
			ext: ".py",
			code: `
def foo(a, b):
    return a + b

class Bar:
    def method(self):
        pass
`,
		},
		{
			ext: ".java",
			code: `
public class Hello {
    public void greet() {
        System.out.println("Hi");
    }
}
`,
		},
	}

	for _, tt := range tests {
		path := writeTempFile(t, tt.ext, tt.code)
		chunks := ProcessFile(path)
		if len(chunks) == 0 {
			t.Fatalf("expected chunks for %s file, got none", tt.ext)
		}

		for _, ch := range chunks {
			checkJSONRoundtrip(t, ch)
		}
	}
}
