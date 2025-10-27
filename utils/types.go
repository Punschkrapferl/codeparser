package utils

type OutputChunk struct {
	Path      string `json:"path"`
	Language  string `json:"language"`
	Code      string `json:"code"`
	StartLine int    `json:"start_line"`
	EndLine   int    `json:"end_line"`
}
