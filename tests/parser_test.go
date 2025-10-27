package utils

import (
	"bufio"
	"bytes"
	"os"
	"testing"

	"codeparser/utils"
)

const pythonSample = `
class AuthService:
    def verify_token(self, token):
        return True
`

const javaSample = `
public class Server {
    public void start() {
        System.out.println("Starting server");
    }
}
`

func TestProcessFilePython(t *testing.T) {
	outBuf := &bytes.Buffer{}
	writer := bufio.NewWriter(outBuf)

	// Write the sample to a temporary file
	tmpFile := "tmp_test.py"
	if err := os.WriteFile(tmpFile, []byte(pythonSample), 0644); err != nil {
		t.Fatal(err)
	}
	defer func() {
		if err := os.Remove(tmpFile); err != nil {
			t.Logf("Failed to remove temp file: %v", err)
		}
	}()

	utils.ProcessFile(tmpFile, writer)

	if err := writer.Flush(); err != nil {
		t.Fatalf("Failed to flush writer: %v", err)
	}

	output := outBuf.String()
	if output == "" {
		t.Fatal("Expected output, got empty string")
	}

	if !bytes.Contains([]byte(output), []byte("AuthService")) {
		t.Fatal("Expected class AuthService in output")
	}
}

func TestProcessFileJava(t *testing.T) {
	outBuf := &bytes.Buffer{}
	writer := bufio.NewWriter(outBuf)

	tmpFile := "TmpTest.java"
	if err := os.WriteFile(tmpFile, []byte(javaSample), 0644); err != nil {
		t.Fatal(err)
	}
	defer func() {
		if err := os.Remove(tmpFile); err != nil {
			t.Logf("Failed to remove temp file: %v", err)
		}
	}()

	utils.ProcessFile(tmpFile, writer)

	if err := writer.Flush(); err != nil {
		t.Fatalf("Failed to flush writer: %v", err)
	}

	output := outBuf.String()
	if output == "" {
		t.Fatal("Expected output, got empty string")
	}

	if !bytes.Contains([]byte(output), []byte("Server")) {
		t.Fatal("Expected class Server in output")
	}
}
