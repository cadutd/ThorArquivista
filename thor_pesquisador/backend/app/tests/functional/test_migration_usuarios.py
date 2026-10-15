import uuid
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from app.core.config import settings
from app.editorial_cli import cadastrar_admin_inicial
from app.schemas.usuario import UsuarioIn
from sqlalchemy.orm import Session


def test_migration_preserva_ids_normaliza_cpf_e_isola_legados(monkeypatch):
    url = make_url(settings.database_url)
    assert url.database.endswith("_test")
    name = "usuarios_migration_" + uuid.uuid4().hex + "_test"
    control = create_engine(url,isolation_level="AUTOCOMMIT")
    temporary = None
    with control.connect() as connection:
        connection.execute(text('CREATE DATABASE "' + name + '"'))
    try:
        temporary_url = url.set(database=name)
        monkeypatch.setattr(settings,"database_url",temporary_url.render_as_string(hide_password=False))
        config = Config("alembic.ini")
        command.upgrade(config,"20261012_000007")
        temporary = create_engine(temporary_url)
        ids = [uuid.uuid4() for _ in range(5)]
        cpfs = ["529.982.247-25","52998224725","invalido",None,"00000000000"]
        subs = ["529.982.247-25","52998224725","legado-invalido","legado-sem-cpf","00000000000"]
        with temporary.begin() as connection:
            for i in range(5):
                connection.execute(text("""INSERT INTO usuarios(id,govbr_sub,cpf,nome,email,criado_em)
                    VALUES(:id,:sub,:cpf,:nome,'legacy@example.org',now() + :i * interval '1 second')"""),
                    dict(id=ids[i],sub=subs[i],cpf=cpfs[i],nome="Legado " + str(i),i=i))
                connection.execute(text("""INSERT INTO sessoes(id,usuario_id,token_hash,expira_em)
                    VALUES(:id,:user,:token,now() + interval '1 hour')"""),
                    dict(id=uuid.uuid4(),user=ids[i],token=uuid.uuid4().hex))
            connection.execute(text("""INSERT INTO acessos_instrumento(id,usuario_id,papel)
                VALUES(:id,:user,'EDITOR')"""),dict(id=uuid.uuid4(),user=ids[0]))
        command.upgrade(config,"20261012_000008")
        with temporary.connect() as connection:
            rows = connection.execute(text("SELECT * FROM usuarios ORDER BY criado_em")).mappings().all()
            assert [r["id"] for r in rows] == ids
            assert rows[0]["cpf"] == "52998224725" and rows[0]["ativo"]
            assert all(not r["ativo"] and r["cpf"] is None for r in rows[1:4])
            assert rows[1]["observacoes"] and rows[2]["observacoes"]
            assert rows[4]["ativo"] and rows[4]["cpf"] == "00000000000"
            assert len({r["username"] for r in rows}) == 5
            assert connection.scalar(text("SELECT count(*) FROM sessoes")) == 2
            assert connection.scalar(text("SELECT origem FROM acessos_instrumento")) == "USUARIO"
        with Session(temporary) as db:
            data = UsuarioIn(nome="Administrador inicial",username="admin_inicial",cpf="11144477735",
                             email="admin@example.org")
            user = cadastrar_admin_inicial(db,data)
            assert user.govbr_sub is None and user.ativo
            with pytest.raises(ValueError,match="administrador ativo"):
                cadastrar_admin_inicial(db,data)
        command.downgrade(config,"20261012_000007")
        with temporary.connect() as connection:
            assert connection.scalar(text("SELECT count(*) FROM usuarios")) == 6
            assert connection.scalar(text("SELECT count(*) FROM usuarios WHERE govbr_sub IS NULL")) == 0
    finally:
        if temporary:
            temporary.dispose()
        with control.connect() as connection:
            connection.execute(text('DROP DATABASE "' + name + '" WITH (FORCE)'))
        control.dispose()
