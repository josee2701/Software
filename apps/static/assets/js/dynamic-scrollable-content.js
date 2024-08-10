function adjustScrollableContentHeight() {
    var scrollableContent = document.getElementById('dynamic-scrollable-content');
    var scrollableContent1 = document.getElementById('dynamic-scrollable-content1');
    var scrollableContent2 = document.getElementById('dynamic-scrollable-content2');

    var vh = window.innerHeight * 0.01;
    var zoomLevel = window.devicePixelRatio;

    if (window.innerHeight > 800) {
        scrollableContent.style.maxHeight = (window.innerHeight - 410) + 'px';
        scrollableContent1.style.maxHeight = (window.innerHeight - 310) + 'px';
        scrollableContent2.style.maxHeight = (window.innerHeight - 410) + 'px';
    } else {
        var adjustedHeight = 33 + ((1 - zoomLevel) * 20); // Ajusta 33vh a 35vh, 40vh, etc.
        var adjustedHeight1 = 60 + ((1 - zoomLevel) * 20); // Ajusta 60vh a 65vh, 70vh, etc.
        var adjustedHeight2 = 40 + ((1 - zoomLevel) * 20);
        
        scrollableContent.style.maxHeight = adjustedHeight + 'vh';
        scrollableContent1.style.maxHeight = adjustedHeight1 + 'vh';
        scrollableContent2.style.maxHeight = adjustedHeight2 + 'vh';
    }
}
document.addEventListener('shown.bs.modal', adjustScrollableContentHeight);
window.addEventListener('resize', adjustScrollableContentHeight);
window.addEventListener('load', adjustScrollableContentHeight);
