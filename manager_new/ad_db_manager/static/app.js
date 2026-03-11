let current=null

async function load(){
    const q=document.getElementById("search").value
    const r=await fetch("/api/dtc/"+q)
    const data=await r.json()

    const table=document.getElementById("table")
    table.innerHTML=""

    for(const d of data){
        const tr=document.createElement("tr")

        const code=document.createElement("td")
        code.innerText=d.code

        const def=document.createElement("td")
        def.innerText=d.definition

        const man=document.createElement("td")
        man.innerText=d.scope.manufacturer

        const btn=document.createElement("button")
        btn.innerText="open"
        btn.onclick=()=>openDTC(d.code)

        const td=document.createElement("td")
        td.appendChild(btn)

        tr.appendChild(code)
        tr.appendChild(def)
        tr.appendChild(man)
        tr.appendChild(td)

        table.appendChild(tr)
    }
}

async function openDTC(code){
    current=code
    const r=await fetch("/api/dtc/"+code)
    const data=await r.json()
    document.getElementById("editor").value=JSON.stringify(data,null,2)
}

async function save(){
    const data=JSON.parse(document.getElementById("editor").value)
    await fetch("/api/dtc/"+data.code,{
        method:"PUT",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify(data)
    })
    load()
}

async function create(){
    const data=JSON.parse(document.getElementById("editor").value)
    await fetch("/api/dtc",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify(data)
    })
    load()
}

async function remove(){
    if(!current) return
    await fetch("/api/dtc/"+current,{method:"DELETE"})
    load()
}

window.onload=load