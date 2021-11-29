package main

import (
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"math/rand"
)

var channel = make(chan int, 10)


func main() {
	channel <- 1
	http.HandleFunc("/convert", handler)
	http.ListenAndServe(":3000", nil)
}

func downloadFile(path string, url string) error {

	// Create the file
	out, err := os.Create(path)
	if err != nil {
		return err
	}
	defer out.Close()

	// Get the data
	resp, err := http.Get(url)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	// Write the body to file
	_, err = io.Copy(out, resp.Body)
	if err != nil {
		return err
	}

	return nil
}

func handler(w http.ResponseWriter, r *http.Request) {


	keys, ok := r.URL.Query()["fileSrc"]

	if !ok || len(keys[0]) < 1 {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("fileSrc Param 'key' is missing"))
		return
	}

	fileSrc := keys[0]

	log.Println("request incoming with fileSrc:",fileSrc)

	workDir := os.TempDir()

	fileName := "document" + fmt.Sprint(rand.Intn(100000))

	inputFile := filepath.Join(workDir, fileName)

	outputFile := filepath.Join(workDir, fileName+".pdf")

	errorDownload := downloadFile(inputFile, fileSrc)

	if errorDownload != nil {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("error when download file"))
		return
	}

	<- channel
	cmd := exec.Command("libreoffice", "--headless", "--convert-to", "pdf", "--outdir", workDir, inputFile)
	_, err := cmd.Output()
	channel <- 1


	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte(err.Error()))
		return
	}

	w.WriteHeader(http.StatusOK)
	w.Header().Set("Content-Type", "application/pdf")

	fileBytes, err := ioutil.ReadFile(outputFile)

	w.Write(fileBytes)

	os.Remove(outputFile)
	os.Remove(inputFile)

	return
}
