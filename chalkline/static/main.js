
function openPopup(id) {
    let pop = document.getElementById('popup_'+id);
    pop.showModal();
}

function closePopup(id) {
    let pop = document.getElementById('popup_'+id);
    pop.close();
}

try {document.getElementById('popup_design').showModal()}
catch {}