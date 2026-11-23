function qAll(s){return encodeURIComponent(s==null?"":String(s));}
/* busi 直调响应外层包一层 data（{errorCode,data:{…}}）；顶层命中即认为已解壳。 */
function unwrapBusi(d){
  if(!d||typeof d!=="object")return d;
  return (d.rule!=null||d.ok!=null||d.groupList!=null)?d:(d.data||d);
}
function busiRule(sn,cabId){
  if(!CFG||!CFG.infoCode)return Promise.reject(new Error('no-infoCode'));
  var base=(CFG.busiRule)||((CFG.host)?('https://'+CFG.host+'/api/portal/mcp/busi/air/domestic/rule'):'');
  if(!base)return Promise.reject(new Error('no-busi'));
  var url=base+'?serialNumber='+qAll(sn)+'&cabId='+qAll(cabId);
  return fetch(url,{headers:{'Accept':'application/json','X-Auth-Code':CFG.infoCode}}).then(function(r){
    return r.json().then(function(raw){
      var body=unwrapBusi(raw);
      if(!r.ok||(body&&body.ok===false))throw new Error((body&&body.message)||(raw&&raw.errorMsg)||('HTTP '+r.status));
      return (body&&body.rule)||body;
    });
  });
}
