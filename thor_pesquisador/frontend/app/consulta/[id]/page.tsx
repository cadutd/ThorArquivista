"use client";
import { useParams } from "next/navigation";
import { PortalRecords } from "@/components/portal-records";
export default function Page(){const {id}=useParams<{id:string}>();return <PortalRecords id={id}/>;}
