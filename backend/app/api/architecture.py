import uuid
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from backend.app.database import get_db
from backend.app.models import ArchitectureModule, ArchitectureRelation, Requirement, Project
from backend.app.schemas import (
    ArchitectureResponse, ArchitectureModuleCreate, ArchitectureModuleUpdate,
    ArchitectureRelationCreate, ArchitectureModuleResponse, ArchitectureRelationResponse
)
from backend.app.agents.architecture_agent import ArchitectureAgent

router = APIRouter(tags=["architecture"])
arch_agent = ArchitectureAgent()


def make_project_scoped_id(project_id: str, logical_id: str) -> str:
    """
    Convert an agent-generated logical ID into a project-scoped DB ID.

    Example:
        MOD-AUTHENTICATION
        -> EC691F0A-MOD-AUTHENTICATION
    """
    if not logical_id:
        return str(uuid.uuid4())

    project_prefix = project_id.replace("-", "")[:8].upper()
    return f"{project_prefix}-{logical_id}"


def build_id_map(project_id: str, items, key: str = "id") -> dict:
    """
    Build logical-ID -> project-scoped-ID mapping.
    """
    result = {}

    for item in items:
        logical_id = item.get(key)

        if logical_id:
            result[logical_id] = make_project_scoped_id(
                project_id,
                logical_id,
            )

    return result

@router.get("/api/projects/{project_id}/architecture", response_model=ArchitectureResponse)
async def get_project_architecture(project_id: str, db: AsyncSession = Depends(get_db)):
    mod_res = await db.execute(select(ArchitectureModule).where(ArchitectureModule.project_id == project_id))
    modules = mod_res.scalars().all()

    rel_res = await db.execute(select(ArchitectureRelation).where(ArchitectureRelation.project_id == project_id))
    relations = rel_res.scalars().all()

    return {
        "modules": modules,
        "relations": relations
    }

@router.post("/api/projects/{project_id}/architecture/generate", response_model=ArchitectureResponse)
async def generate_architecture(project_id: str, db: AsyncSession = Depends(get_db)):
    p_res = await db.execute(select(Project).where(Project.id == project_id))
    project = p_res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    r_res = await db.execute(select(Requirement).where(Requirement.project_id == project_id))
    requirements = [
        {"id": r.id, "req_type": r.req_type, "summary": r.summary, "description": r.description, "actor": r.actor, "action": r.action, "target_object": r.target_object}
        for r in r_res.scalars().all()
    ]

    generated = arch_agent.generate_architecture(requirements, project.title)

    # Clear old
    await db.execute(delete(ArchitectureRelation).where(ArchitectureRelation.project_id == project_id))
    await db.execute(delete(ArchitectureModule).where(ArchitectureModule.project_id == project_id))

    module_id_map = build_id_map(
        project_id,
        generated["modules"],
    )

    new_modules = []
    for m in generated["modules"]:
        logical_module_id = m["id"]
        db_module_id = module_id_map.get(
            logical_module_id,
            make_project_scoped_id(
                project_id,
                logical_module_id,
            ),
        )

        mod_obj = ArchitectureModule(
            id=db_module_id,
            project_id=project_id,
            name=m["name"],
            description=m.get("description", ""),
            module_type=m.get("module_type", "service"),
            tech_stack=m.get("tech_stack", ""),
            responsibilities=m.get("responsibilities", []),
            api_endpoints=m.get("api_endpoints", []),
            pos_x=m.get("pos_x", 100.0),
            pos_y=m.get("pos_y", 100.0),
            is_ai_suggested=True,
            status="approved"
        )
        db.add(mod_obj)
        new_modules.append(mod_obj)
    await db.flush()

    new_relations = []
    for rel in generated["relations"]:
        logical_source = rel.get("source_module_id")
        logical_target = rel.get("target_module_id")

        mapped_source = module_id_map.get(logical_source)
        mapped_target = module_id_map.get(logical_target)

        # Never create a relation to a nonexistent module.
        if not mapped_source or not mapped_target:
            continue

        rel_obj = ArchitectureRelation(
            id=str(uuid.uuid4()),
            project_id=project_id,
            source_module_id=mapped_source,
            target_module_id=mapped_target,
            relation_type=rel.get("relation_type", "calls"),
            description=rel.get("description", "")
        )
        db.add(rel_obj)
        new_relations.append(rel_obj)

    await db.commit()
    return {
        "modules": new_modules,
        "relations": new_relations
    }

@router.post("/api/projects/{project_id}/architecture/modules", response_model=ArchitectureModuleResponse)
async def create_module(project_id: str, mod_in: ArchitectureModuleCreate, db: AsyncSession = Depends(get_db)):
    mod_id = mod_in.id or f"MOD-{uuid.uuid4().hex[:6].upper()}"
    new_mod = ArchitectureModule(
        id=mod_id,
        project_id=project_id,
        name=mod_in.name,
        description=mod_in.description or "",
        module_type=mod_in.module_type or "service",
        tech_stack=mod_in.tech_stack or "",
        responsibilities=mod_in.responsibilities or [],
        api_endpoints=mod_in.api_endpoints or [],
        pos_x=mod_in.pos_x or 200.0,
        pos_y=mod_in.pos_y or 200.0,
        is_ai_suggested=False,
        status="approved"
    )
    db.add(new_mod)
    await db.commit()
    await db.refresh(new_mod)
    return new_mod

@router.patch("/api/architecture/modules/{id}", response_model=ArchitectureModuleResponse)
async def update_module(id: str, mod_in: ArchitectureModuleUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ArchitectureModule).where(ArchitectureModule.id == id))
    mod = res.scalars().first()
    if not mod:
        raise HTTPException(status_code=404, detail="Module not found")

    if mod_in.name is not None:
        mod.name = mod_in.name
    if mod_in.description is not None:
        mod.description = mod_in.description
    if mod_in.module_type is not None:
        mod.module_type = mod_in.module_type
    if mod_in.tech_stack is not None:
        mod.tech_stack = mod_in.tech_stack
    if mod_in.responsibilities is not None:
        mod.responsibilities = mod_in.responsibilities
    if mod_in.api_endpoints is not None:
        mod.api_endpoints = mod_in.api_endpoints
    if mod_in.pos_x is not None:
        mod.pos_x = mod_in.pos_x
    if mod_in.pos_y is not None:
        mod.pos_y = mod_in.pos_y
    if mod_in.status is not None:
        mod.status = mod_in.status

    await db.commit()
    await db.refresh(mod)
    return mod

@router.post("/api/projects/{project_id}/architecture/relations", response_model=ArchitectureRelationResponse)
async def create_relation(project_id: str, rel_in: ArchitectureRelationCreate, db: AsyncSession = Depends(get_db)):
    rel = ArchitectureRelation(
        id=str(uuid.uuid4()),
        project_id=project_id,
        source_module_id=rel_in.source_module_id,
        target_module_id=rel_in.target_module_id,
        relation_type=rel_in.relation_type or "calls",
        description=rel_in.description or ""
    )
    db.add(rel)
    await db.commit()
    await db.refresh(rel)
    return rel
