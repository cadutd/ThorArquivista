# Padrao Lazy Tree Full-Stack

Use este guia para implementar arvores navegaveis com lazy load em qualquer modulo hierarquico do Thor. Adapte nomes, rotas, bibliotecas e tipos aos padroes locais do projeto.

## Backend

### Modelo e banco

Modele a hierarquia com uma chave estrangeira opcional para o pai:

```py
class Entity(Base):
    __tablename__ = "entities"

    id = Column(UUID, primary_key=True)
    name = Column(String, nullable=False)
    parent_id = Column(UUID, ForeignKey("entities.id", ondelete="SET NULL"), nullable=True, index=True)
```

Adicione indice para a coluna de pai e para filtros usados na arvore. Quando a ordem visual importa, inclua campo de ordenacao e aplique ordenacao deterministica.

### Schema de no

O no da arvore deve ser pequeno:

```py
class EntityTreeNode(BaseModel):
    id: UUID
    name: str
    parent_id: UUID | None = None
    has_children: bool = False
    children: list["EntityTreeNode"] = Field(default_factory=list)
```

Nao inclua textos longos, blobs, historico, auditoria extensa ou dados de detalhe na resposta da arvore. Busque esses dados no endpoint de detalhe.

### Servico de arvore

Implemente duas consultas principais: raiz/recorte inicial e filhos diretos por pai.

```py
def list_tree(db: Session, parent_id: UUID | None = None, q: str | None = None) -> list[EntityTreeNode]:
    query = db.query(Entity)

    if parent_id is not None:
        query = query.filter(Entity.parent_id == parent_id)
    else:
        query = query.filter(Entity.parent_id.is_(None))

    if q:
        query = query.filter(Entity.name.ilike(f"%{q}%"))

    records = query.order_by(Entity.name.asc()).all()
    return [to_tree_node(db, record) for record in records]

def to_tree_node(db: Session, record: Entity) -> EntityTreeNode:
    has_children = db.query(Entity.id).filter(Entity.parent_id == record.id).first() is not None
    return EntityTreeNode(
        id=record.id,
        name=record.name,
        parent_id=record.parent_id,
        has_children=has_children,
        children=[],
    )
```

Evite montar a arvore recursivamente no backend para a tela lazy. A resposta deve ser pequena e previsivel.

### Validacao de hierarquia

Quando o pai puder ser alterado, valide no servico:

```py
def validate_parent(db: Session, entity_id: UUID | None, parent_id: UUID | None) -> None:
    if parent_id is None:
        return
    if entity_id is not None and parent_id == entity_id:
        raise ValueError("O registro nao pode ser pai de si mesmo.")

    parent = db.get(Entity, parent_id)
    if parent is None:
        raise ValueError("Registro pai nao encontrado.")

    current = parent
    while current is not None:
        if entity_id is not None and current.parent_id == entity_id:
            raise ValueError("A hierarquia nao pode conter ciclos.")
        current = db.get(Entity, current.parent_id) if current.parent_id else None
```

Se o dominio tiver niveis controlados, valide tambem quais niveis podem ser filhos de cada pai.

### Rotas

Use nomes coerentes com o projeto, mantendo este contrato:

```text
GET /api/v1/entities/tree
GET /api/v1/entities/tree?parent_id=<id>
GET /api/v1/entities/{id}
```

O endpoint de arvore retorna lista de nos. O endpoint de detalhe retorna o registro completo.

## Frontend

### Tipo base

```ts
type TreeNode = {
  id: string;
  name: string;
  parent_id?: string | null;
  has_children: boolean;
  children: TreeNode[];
};
```

Use `children`, `filhos` ou outro campo equivalente conforme o contrato do backend.

### Estado

```ts
const [expanded, setExpanded] = useState<Set<string>>(new Set());
const [treeChildren, setTreeChildren] = useState<Record<string, TreeNode[]>>({});
const [loadingTreeNodes, setLoadingTreeNodes] = useState<Set<string>>(new Set());
const [selectedId, setSelectedId] = useState<string | null>(null);
```

### Carga inicial e filhos

```ts
const tree = useQuery({
  queryKey: ["entities", "tree", filters],
  queryFn: () => listTree(filters),
});

const toggleTreeNode = async (node: TreeNode) => {
  setExpanded((current) => toggleSet(current, node.id));
  if (!node.has_children || treeChildren[node.id]) return;

  setLoadingTreeNodes((current) => new Set(current).add(node.id));
  try {
    const children = await queryClient.fetchQuery({
      queryKey: ["entities", "tree", "children", node.id],
      queryFn: () => listTree({ parent_id: node.id }),
    });
    setTreeChildren((current) => ({ ...current, [node.id]: children }));
  } finally {
    setLoadingTreeNodes((current) => {
      const next = new Set(current);
      next.delete(node.id);
      return next;
    });
  }
};
```

### Hidratacao local

```ts
function hydrateTreeNodes(nodes: TreeNode[], childrenByParent: Record<string, TreeNode[]>): TreeNode[] {
  return nodes.map((node) => ({
    ...node,
    children: hydrateTreeNodes(childrenByParent[node.id] ?? node.children, childrenByParent),
  }));
}
```

### Selecao e detalhe

Ao selecionar um no, guarde apenas o `id` e busque o detalhe separadamente:

```ts
const detail = useQuery({
  queryKey: ["entities", selectedId],
  queryFn: () => getEntity(selectedId as string),
  enabled: Boolean(selectedId),
});
```

### Reset por filtros

Quando busca ou filtros mudarem, limpe a navegacao local:

```ts
useEffect(() => {
  setExpanded(new Set());
  setTreeChildren({});
  setLoadingTreeNodes(new Set());
}, [search, statusFilter, typeFilter]);
```

### Renderizacao

O componente de no deve receber `node`, `level`, `selectedId`, `expanded`, `loadingIds`, `onToggle` e `onSelect`. Use um botao de expansao com dimensao fixa, indicador de loading por no e indentacao baseada no nivel.

Nao renderize recursivamente dados que ainda nao foram carregados. Se `has_children` for verdadeiro e o no estiver aberto, renderize apenas a lista presente no campo de filhos hidratado.

## Invalidacao

Depois de criar, editar, excluir, mover ou reordenar um no:

- invalide a consulta raiz da arvore
- invalide a consulta de filhos do pai anterior, quando houver
- invalide a consulta de filhos do novo pai, quando houver
- invalide o detalhe do registro alterado
- limpe estado local quando a mudanca puder deixar a arvore inconsistente

## Verificacao

Backend:

- rota raiz retorna apenas raizes ou o recorte inicial
- rota com `parent_id` retorna somente filhos diretos
- `has_children` e verdadeiro para pai com filho
- filhos vem como lista vazia na resposta lazy
- autorreferencia e ciclos sao rejeitados

Frontend:

- estado inicial mostra raizes
- expandir no com filhos chama a busca com `parent_id`
- expandir novamente nao refaz a busca se filhos ja estao em cache local
- spinner aparece apenas no no carregando
- selecionar no busca detalhe por `id`
- mudar filtros limpa expansao e filhos carregados
