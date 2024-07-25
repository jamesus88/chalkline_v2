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
        count--;
    }

    return page
}

let page = 1
let tbl = document.getElementById('schedule-table');
colorifySchedule(tbl);
loadMore(tbl, page, 50);

function load() {
    page = loadMore(tbl, page + 1, 50);
    if (page == 0) {
        let button = document.getElementById('load-more');
        button.classList.add('disabled');
        button.disabled = true;
        button.innerHTML = "All Events Shown";
    }
}

function openPopup(id) {
    let pop = document.getElementById('popup_'+id);
    pop.showModal();
}

function closePopup(id) {
    let pop = document.getElementById('popup_'+id);
    pop.close();
}

function toggleFilterSection(section) {
    let sect = document.getElementById(section);
    if (sect.style.display == 'block') {
        sect.style.display = 'none';
    }
    else {
        sect.style.display = 'block';
    }
}
