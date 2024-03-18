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

function loadMore(tbl, page, limit) {
    for (let i = 0; i < tbl.rows.length; i++) {
        tbl.rows[i].style.display = "";
    }

    let count = tbl.rows.length - 1;
    if (count < limit * page) {
        return 0
    }

    while (count > (limit * page)) {
        tbl.rows[count].style.display = "none";
        count--
    }

    return page
}

console.log('schedule.js loaded')