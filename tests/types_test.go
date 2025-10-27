package utils

import (
	"encoding/json"
	"testing"

	"codeparser/utils"
)

func TestOutputChunkJSON(t *testing.T) {
	chunk := utils.OutputChunk{
		Path:      "example.py",
		Language:  "python",
		Code:      "def foo(): pass",
		StartLine: 1,
		EndLine:   1,
	}

	data, err := json.Marshal(chunk)
	if err != nil {
		t.Fatalf("Failed to marshal OutputChunk: %v", err)
	}

	var unmarshalled utils.OutputChunk
	if err := json.Unmarshal(data, &unmarshalled); err != nil {
		t.Fatalf("Failed to unmarshal OutputChunk: %v", err)
	}

	if unmarshalled.Path != chunk.Path ||
		unmarshalled.Language != chunk.Language ||
		unmarshalled.Code != chunk.Code ||
		unmarshalled.StartLine != chunk.StartLine ||
		unmarshalled.EndLine != chunk.EndLine {
		t.Fatal("Unmarshalled OutputChunk does not match original")
	}
}
