from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.dependencias import get_db, get_usuario_actual
from app.models import Rol, Usuario
from app.schemas.auth import LoginEntrada, RegistroEntrada, UsuarioPublico
from app.seguridad import borrar_cookie, establecer_cookie, hash_password, verificar_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/registro", response_model=UsuarioPublico, status_code=status.HTTP_201_CREATED)
def registro(datos: RegistroEntrada, response: Response, db: Session = Depends(get_db)) -> Usuario:
    if db.query(Usuario).filter_by(email=datos.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El correo ya está registrado")
    if db.query(Usuario).filter_by(apodo=datos.apodo).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El apodo ya está en uso")

    usuario = Usuario(
        email=datos.email,
        apodo=datos.apodo,
        password_hash=hash_password(datos.password),
        rol=Rol.USER,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    establecer_cookie(response, usuario.id)
    return usuario


@router.post("/login", response_model=UsuarioPublico)
def login(datos: LoginEntrada, response: Response, db: Session = Depends(get_db)) -> Usuario:
    usuario = db.query(Usuario).filter_by(email=datos.email).first()
    if usuario is None or not verificar_password(datos.password, usuario.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    establecer_cookie(response, usuario.id)
    return usuario


@router.post("/logout")
def logout(response: Response) -> dict:
    borrar_cookie(response)
    return {"ok": True}


@router.get("/yo", response_model=UsuarioPublico)
def yo(usuario: Usuario = Depends(get_usuario_actual)) -> Usuario:
    return usuario
