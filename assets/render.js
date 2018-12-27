console.log("we are here");

document.addEventListener("DOMContentLoaded", function(event) {
    //do work

    spans = document.getElementsByTagName("span");
    console.log(spans.length + "found");
    for(let span of spans)
    {
        if(span.getAttribute("data-type") == "formula")
        {
            var d=document.createElement("span");
            var code=span.getAttribute("data-value");
            katex.render(code,d,{ throwOnError: false });
            var p=span.parentNode;
            p.insertBefore(d,span);
            span.remove();
        }
        //spans[i].innerHTML="here be dragons";
        //console.log("iterated");

    }
});

