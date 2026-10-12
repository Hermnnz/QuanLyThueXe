-- Fleet integration 19.0.5.1.0, snapshot 2026-10-12.

-- Schema-only, includes Odoo core fields; NOT an Odoo installer or migration.

-- Use only an isolated schema with shared Odoo reference tables available.

-- Fleet methods and workflow live in ORM, not in this schema export.

-- UTC timestamps; ORM defaults/ACL are not represented as SQL logic.

BEGIN;

CREATE TABLE "fleet_vehicle" (
    "id" serial NOT NULL,
    "manager_id" integer,
    "company_id" integer,
    "driver_id" integer,
    "future_driver_id" integer,
    "model_id" integer NOT NULL,
    "brand_id" integer,
    "state_id" integer,
    "seats" integer,
    "doors" integer,
    "category_id" integer,
    "vehicle_range" integer,
    "create_uid" integer,
    "write_uid" integer,
    "name" character varying,
    "license_plate" character varying,
    "vin_sn" character varying,
    "color" character varying,
    "location" character varying,
    "model_year" character varying,
    "odometer_unit" character varying NOT NULL,
    "transmission" character varying,
    "fuel_type" character varying,
    "power_unit" character varying NOT NULL,
    "co2_emission_unit" character varying NOT NULL,
    "co2_standard" character varying,
    "frame_type" character varying,
    "range_unit" character varying NOT NULL,
    "next_assignation_date" date,
    "order_date" date,
    "acquisition_date" date,
    "write_off_date" date,
    "contract_date_start" date,
    "vehicle_properties" jsonb,
    "description" text,
    "active" boolean,
    "trailer_hook" boolean,
    "plan_to_change_car" boolean,
    "plan_to_change_bike" boolean,
    "electric_assistance" boolean,
    "create_date" timestamp without time zone,
    "write_date" timestamp without time zone,
    "horsepower" double precision,
    "horsepower_tax" double precision,
    "power" double precision,
    "co2" double precision,
    "car_value" double precision,
    "net_car_value" double precision,
    "residual_value" double precision,
    "frame_size" double precision,
    "vehicle_code" character varying,
    "operational_status" character varying NOT NULL,
    "next_service_date" date,
    "block_reason" text,
    "is_electric_motorbike" boolean,
    "technical_ready" boolean,
    "rental_blocked" boolean
);

CREATE TABLE "fleet_vehicle_log_services" (
    "id" serial NOT NULL,
    "vehicle_id" integer NOT NULL,
    "model_id" integer,
    "brand_id" integer,
    "manager_id" integer,
    "odometer_id" integer,
    "company_id" integer,
    "purchaser_id" integer,
    "vendor_id" integer,
    "service_type_id" integer NOT NULL,
    "create_uid" integer,
    "write_uid" integer,
    "description" character varying,
    "inv_ref" character varying,
    "state" character varying,
    "date" date,
    "notes" text,
    "amount" numeric,
    "active" boolean,
    "create_date" timestamp without time zone,
    "write_date" timestamp without time zone,
    "technician_id" integer,
    "maintenance_type" character varying NOT NULL,
    "next_service_date" date,
    "result" text,
    "blocks_rental" boolean,
    "scheduled_start" timestamp without time zone,
    "scheduled_end" timestamp without time zone,
    "actual_start" timestamp without time zone,
    "actual_end" timestamp without time zone
);

ALTER TABLE "fleet_vehicle" ADD CONSTRAINT "fleet_vehicle_brand_id_fkey" FOREIGN KEY (brand_id) REFERENCES fleet_vehicle_model_brand(id) ON DELETE SET NULL;

ALTER TABLE "fleet_vehicle" ADD CONSTRAINT "fleet_vehicle_category_id_fkey" FOREIGN KEY (category_id) REFERENCES fleet_vehicle_model_category(id) ON DELETE SET NULL;

ALTER TABLE "fleet_vehicle" ADD CONSTRAINT "fleet_vehicle_company_id_fkey" FOREIGN KEY (company_id) REFERENCES res_company(id) ON DELETE SET NULL;

ALTER TABLE "fleet_vehicle" ADD CONSTRAINT "fleet_vehicle_create_uid_fkey" FOREIGN KEY (create_uid) REFERENCES res_users(id) ON DELETE SET NULL;

ALTER TABLE "fleet_vehicle" ADD CONSTRAINT "fleet_vehicle_driver_id_fkey" FOREIGN KEY (driver_id) REFERENCES res_partner(id) ON DELETE SET NULL;

ALTER TABLE "fleet_vehicle" ADD CONSTRAINT "fleet_vehicle_future_driver_id_fkey" FOREIGN KEY (future_driver_id) REFERENCES res_partner(id) ON DELETE SET NULL;

ALTER TABLE "fleet_vehicle" ADD CONSTRAINT "fleet_vehicle_manager_id_fkey" FOREIGN KEY (manager_id) REFERENCES res_users(id) ON DELETE SET NULL;

ALTER TABLE "fleet_vehicle" ADD CONSTRAINT "fleet_vehicle_model_id_fkey" FOREIGN KEY (model_id) REFERENCES fleet_vehicle_model(id) ON DELETE RESTRICT;

ALTER TABLE "fleet_vehicle" ADD CONSTRAINT "fleet_vehicle_pkey" PRIMARY KEY (id);

ALTER TABLE "fleet_vehicle" ADD CONSTRAINT "fleet_vehicle_state_id_fkey" FOREIGN KEY (state_id) REFERENCES fleet_vehicle_state(id) ON DELETE SET NULL;

ALTER TABLE "fleet_vehicle" ADD CONSTRAINT "fleet_vehicle_vehicle_code_unique" UNIQUE (vehicle_code);

ALTER TABLE "fleet_vehicle" ADD CONSTRAINT "fleet_vehicle_write_uid_fkey" FOREIGN KEY (write_uid) REFERENCES res_users(id) ON DELETE SET NULL;

CREATE INDEX fleet_vehicle__vehicle_code_index ON fleet_vehicle USING btree (vehicle_code);

ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_brand_id_fkey" FOREIGN KEY (brand_id) REFERENCES fleet_vehicle_model_brand(id) ON DELETE SET NULL;

ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_company_id_fkey" FOREIGN KEY (company_id) REFERENCES res_company(id) ON DELETE SET NULL;

ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_create_uid_fkey" FOREIGN KEY (create_uid) REFERENCES res_users(id) ON DELETE SET NULL;

ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_manager_id_fkey" FOREIGN KEY (manager_id) REFERENCES res_users(id) ON DELETE SET NULL;

ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_model_id_fkey" FOREIGN KEY (model_id) REFERENCES fleet_vehicle_model(id) ON DELETE SET NULL;

ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_odometer_id_fkey" FOREIGN KEY (odometer_id) REFERENCES fleet_vehicle_odometer(id) ON DELETE SET NULL;

ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_pkey" PRIMARY KEY (id);

ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_purchaser_id_fkey" FOREIGN KEY (purchaser_id) REFERENCES res_partner(id) ON DELETE SET NULL;

ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_service_type_id_fkey" FOREIGN KEY (service_type_id) REFERENCES fleet_service_type(id) ON DELETE RESTRICT;

ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_technician_id_fkey" FOREIGN KEY (technician_id) REFERENCES res_partner(id) ON DELETE SET NULL;

ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_vehicle_id_fkey" FOREIGN KEY (vehicle_id) REFERENCES fleet_vehicle(id) ON DELETE RESTRICT;

ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_vendor_id_fkey" FOREIGN KEY (vendor_id) REFERENCES res_partner(id) ON DELETE SET NULL;

ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_write_uid_fkey" FOREIGN KEY (write_uid) REFERENCES res_users(id) ON DELETE SET NULL;

CREATE INDEX fleet_vehicle_log_services__vehicle_id_index ON fleet_vehicle_log_services USING btree (vehicle_id);

COMMIT;
