const input = document.getElementById("search-input");

  input.addEventListener("keyup", (e) => {
    const value = e.target.value.toLowerCase();
    // Obtener todas las filas de la tabla
    const rows = document.querySelector("tbody").querySelectorAll("tr");

    rows.forEach((row) => {
      // Obtener el texto de todas las celdas en la fila
      const cellTexts = Array.from(row.querySelectorAll("td")).map(cell => cell.textContent.toLowerCase());

      // Si alguna de las celdas contiene el valor buscado, mostrar la fila
      if (cellTexts.some(text => text.includes(value))) {
        row.hidden = false;
      } else {
        row.hidden = true;
      }
    });
  });
