

class JSScript:
    GET_ELEMENT_RECT_SCRIPT = """
    const r = arguments[0].getBoundingClientRect();
    return {
        cx: Math.floor(r.left + r.width / 2),
        cy: Math.floor(r.top + r.height / 2),
        w: r.width, 
        h: r.height
    };
    """

    GET_VIEWPORT_SIZE_SCRIPT = """
    return [
        window.innerWidth || document.documentElement.clientWidth,
        window.innerHeight || document.documentElement.clientHeight
    ];
    """

    CENTER_COORDS_SCRIPT = """
                const r = arguments[0].getBoundingClientRect();
                return [Math.floor(r.left + r.width/2), Math.floor(r.top + r.height/2)];
            """

    TOP_EL_SCRIPT = "return document.elementFromPoint(arguments[0], arguments[1]);"

    IS_DESCENDANT_SCRIPT = "return arguments[0].contains(arguments[1]);"

    GET_CURRENT_STYLE = "return arguments[0].getAttribute('style')||'';"
    SET_NEW_STYLE = "arguments[0].setAttribute('style', (arguments[1] ? arguments[1]+';' : '') + arguments[2]);"


