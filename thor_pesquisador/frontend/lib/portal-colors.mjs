export function colorErrors(colors) {
  const errors={};
  for(const [key,value] of Object.entries(colors))if(!/^#[0-9a-f]{6}$/i.test(value))errors["cores."+key]="Use #RRGGBB.";
  if(Object.keys(errors).length)return errors;
  const lum=value=>{
    const values=[1,3,5].map(i=>parseInt(value.slice(i,i+2),16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);
    return values.reduce((sum,value,i)=>sum+value*[.2126,.7152,.0722][i],0);
  };
  const contrast=(a,b)=>{const values=[lum(a),lum(b)].sort((a,b)=>a-b);return (values[1]+.05)/(values[0]+.05);};
  for(const key of ["texto","primaria","secundaria","destaque"])if(contrast(colors[key],colors.fundo)<4.5)
    errors["cores."+key]="Contraste minimo com o fundo: 4,5:1.";
  return errors;
}
