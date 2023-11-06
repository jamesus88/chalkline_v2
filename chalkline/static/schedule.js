function colorifySchedule(tbl) {
    for (let i = 0, row; row = tbl.rows[i]; i++) {
        let text = row.cells[1].innerHTML;
        if (text == 'Game') {
            row.cells[1].classList.add('red-text');
        }
        else if (text == 'Practice') {
            row.cells[1].classList.add('green-text');
        }
        else if (text == 'Umpire Duty') {
            row.cells[1].classList.add('blue-text');
        }
    }
}
console.log('schedule.js loaded')