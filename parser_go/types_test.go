package main

import (
	"encoding/json"
	"testing"
)

func TestOutputChunkJSONMarshalling(t *testing.T) {
	chunk := OutputChunk{
		Path:      "/tmp/test.py",
		Language:  "python",
		Code:      "def foo(): pass",
		StartLine: 1,
		EndLine:   2,
	}

	data, err := json.Marshal(chunk)
	if err != nil {
		t.Fatalf("unexpected marshal error: %v", err)
	}

	var decoded map[string]interface{}
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("unexpected unmarshal error: %v", err)
	}

	// Check JSON field names
	if _, ok := decoded["path"]; !ok {
		t.Error("expected field path in JSON")
	}
	if _, ok := decoded["language"]; !ok {
		t.Error("expected field language in JSON")
	}
	if _, ok := decoded["code"]; !ok {
		t.Error("expected field code in JSON")
	}
	if _, ok := decoded["start_line"]; !ok {
		t.Error("expected field start_line in JSON")
	}
	if _, ok := decoded["end_line"]; !ok {
		t.Error("expected field end_line in JSON")
	}

	// Check values
	if decoded["path"] != "/tmp/test.py" {
		t.Errorf("unexpected path value: %v", decoded["path"])
	}
	if decoded["language"] != "python" {
		t.Errorf("unexpected language value: %v", decoded["language"])
	}
	if decoded["code"] != "def foo(): pass" {
		t.Errorf("unexpected code value: %v", decoded["code"])
	}
	if int(decoded["start_line"].(float64)) != 1 {
		t.Errorf("unexpected start_line value: %v", decoded["start_line"])
	}
	if int(decoded["end_line"].(float64)) != 2 {
		t.Errorf("unexpected end_line value: %v", decoded["end_line"])
	}
}

func TestOutputChunkJSONUnmarshalling(t *testing.T) {
	jsonData := []byte(`{
		"path": "src/main.java",
		"language": "java",
		"code": "class A {}",
		"start_line": 10,
		"end_line": 20
	}`)

	var chunk OutputChunk
	if err := json.Unmarshal(jsonData, &chunk); err != nil {
		t.Fatalf("unexpected unmarshal error: %v", err)
	}

	if chunk.Path != "src/main.java" {
		t.Errorf("wrong Path. got %s", chunk.Path)
	}
	if chunk.Language != "java" {
		t.Errorf("wrong Language. got %s", chunk.Language)
	}
	if chunk.Code != "class A {}" {
		t.Errorf("wrong Code. got %s", chunk.Code)
	}
	if chunk.StartLine != 10 {
		t.Errorf("wrong StartLine. got %d", chunk.StartLine)
	}
	if chunk.EndLine != 20 {
		t.Errorf("wrong EndLine. got %d", chunk.EndLine)
	}
}
