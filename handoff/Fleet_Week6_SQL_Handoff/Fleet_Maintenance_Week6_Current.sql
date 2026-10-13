-- FLEET & MAINTENANCE - CURRENT IMPLEMENTATION, WEEK 5 + WEEK 6
-- Odoo 19, module motorbike_fleet_management 19.0.2.0.0, commit b8ae865.
-- Schema-only snapshot, verified on 2026-10-02. No business data or credentials.
-- For schema review / consolidation, NOT an Odoo module installer or upgrade.
-- These six table names must NOT already exist in the target schema.
-- The three fleet_* tables include their inherited Odoo core columns.
-- External referenced tables must exist first (see README.md).
-- Use an isolated schema/database for SQL experiments, never run over live Odoo.
-- Odoo defaults, computed fields, Python constraints, ACL and UI are NOT SQL DDL.
-- Do not add SQL defaults/checks and call them current implementation.
-- All timestamps below are PostgreSQL timestamp without time zone (Odoo UTC).

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
    "battery_serial" character varying,
    "battery_warranty_until" date,
    "is_electric_motorbike" boolean,
    "battery_capacity_kwh" double precision,
    "battery_voltage" double precision,
    "battery_health" double precision,
    "charging_time_hours" double precision,
    "current_battery_id" integer,
    "vehicle_code" character varying,
    "lifecycle_status" character varying NOT NULL,
    "operational_status" character varying NOT NULL,
    "next_service_date" date,
    "block_reason" text,
    "technical_ready" boolean,
    "rental_blocked" boolean,
    "min_rental_soc" double precision,
    "next_service_odo" double precision
);

CREATE TABLE "fleet_vehicle_odometer" (
    "id" serial NOT NULL,
    "vehicle_id" integer NOT NULL,
    "driver_id" integer,
    "create_uid" integer,
    "write_uid" integer,
    "name" character varying,
    "date" date,
    "create_date" timestamp without time zone,
    "write_date" timestamp without time zone,
    "value" double precision,
    "service_id" integer,
    "source_type" character varying NOT NULL,
    "note" text
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
    "maintenance_component" character varying NOT NULL,
    "next_maintenance_date" date,
    "maintenance_result" text,
    "maintenance_type" character varying NOT NULL,
    "blocks_rental" boolean,
    "scheduled_start" timestamp without time zone,
    "scheduled_end" timestamp without time zone,
    "actual_start" timestamp without time zone,
    "actual_end" timestamp without time zone
);

CREATE TABLE "motorbike_battery" (
    "id" serial NOT NULL,
    "cycle_count" integer,
    "create_uid" integer,
    "write_uid" integer,
    "battery_code" character varying NOT NULL,
    "serial_number" character varying,
    "status" character varying NOT NULL,
    "warranty_expiry" date,
    "active" boolean,
    "create_date" timestamp without time zone,
    "write_date" timestamp without time zone,
    "capacity_kwh" double precision,
    "voltage" double precision,
    "soc" double precision,
    "soh" double precision
);

CREATE TABLE "motorbike_battery_assignment" (
    "id" serial NOT NULL,
    "battery_id" integer NOT NULL,
    "vehicle_id" integer NOT NULL,
    "create_uid" integer,
    "write_uid" integer,
    "reason" text,
    "installed_at" timestamp without time zone NOT NULL,
    "removed_at" timestamp without time zone,
    "create_date" timestamp without time zone,
    "write_date" timestamp without time zone,
    "install_odo" double precision,
    "remove_odo" double precision
);

CREATE TABLE "motorbike_maintenance_plan" (
    "id" serial NOT NULL,
    "vehicle_id" integer NOT NULL,
    "service_type_id" integer,
    "interval_days" integer,
    "warning_days" integer,
    "create_uid" integer,
    "write_uid" integer,
    "name" character varying NOT NULL,
    "last_service_date" date,
    "next_service_date" date,
    "active" boolean,
    "create_date" timestamp without time zone,
    "write_date" timestamp without time zone,
    "interval_km" double precision,
    "last_service_odo" double precision,
    "next_service_odo" double precision,
    "warning_km" double precision
);

-- PRIMARY KEYS AND UNIQUE CONSTRAINTS
ALTER TABLE "fleet_vehicle" ADD CONSTRAINT "fleet_vehicle_pkey" PRIMARY KEY (id);
ALTER TABLE "fleet_vehicle_odometer" ADD CONSTRAINT "fleet_vehicle_odometer_pkey" PRIMARY KEY (id);
ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_pkey" PRIMARY KEY (id);
ALTER TABLE "motorbike_battery" ADD CONSTRAINT "motorbike_battery_pkey" PRIMARY KEY (id);
ALTER TABLE "motorbike_battery" ADD CONSTRAINT "motorbike_battery_code_unique" UNIQUE (battery_code);
ALTER TABLE "motorbike_battery" ADD CONSTRAINT "motorbike_battery_serial_unique" UNIQUE (serial_number);
ALTER TABLE "motorbike_battery_assignment" ADD CONSTRAINT "motorbike_battery_assignment_pkey" PRIMARY KEY (id);
ALTER TABLE "motorbike_maintenance_plan" ADD CONSTRAINT "motorbike_maintenance_plan_pkey" PRIMARY KEY (id);

-- FOREIGN KEYS
ALTER TABLE "fleet_vehicle" ADD CONSTRAINT "fleet_vehicle_brand_id_fkey" FOREIGN KEY (brand_id) REFERENCES fleet_vehicle_model_brand(id) ON DELETE SET NULL;
ALTER TABLE "fleet_vehicle" ADD CONSTRAINT "fleet_vehicle_category_id_fkey" FOREIGN KEY (category_id) REFERENCES fleet_vehicle_model_category(id) ON DELETE SET NULL;
ALTER TABLE "fleet_vehicle" ADD CONSTRAINT "fleet_vehicle_company_id_fkey" FOREIGN KEY (company_id) REFERENCES res_company(id) ON DELETE SET NULL;
ALTER TABLE "fleet_vehicle" ADD CONSTRAINT "fleet_vehicle_create_uid_fkey" FOREIGN KEY (create_uid) REFERENCES res_users(id) ON DELETE SET NULL;
ALTER TABLE "fleet_vehicle" ADD CONSTRAINT "fleet_vehicle_current_battery_id_fkey" FOREIGN KEY (current_battery_id) REFERENCES motorbike_battery(id) ON DELETE SET NULL;
ALTER TABLE "fleet_vehicle" ADD CONSTRAINT "fleet_vehicle_driver_id_fkey" FOREIGN KEY (driver_id) REFERENCES res_partner(id) ON DELETE SET NULL;
ALTER TABLE "fleet_vehicle" ADD CONSTRAINT "fleet_vehicle_future_driver_id_fkey" FOREIGN KEY (future_driver_id) REFERENCES res_partner(id) ON DELETE SET NULL;
ALTER TABLE "fleet_vehicle" ADD CONSTRAINT "fleet_vehicle_manager_id_fkey" FOREIGN KEY (manager_id) REFERENCES res_users(id) ON DELETE SET NULL;
ALTER TABLE "fleet_vehicle" ADD CONSTRAINT "fleet_vehicle_model_id_fkey" FOREIGN KEY (model_id) REFERENCES fleet_vehicle_model(id) ON DELETE RESTRICT;
ALTER TABLE "fleet_vehicle" ADD CONSTRAINT "fleet_vehicle_state_id_fkey" FOREIGN KEY (state_id) REFERENCES fleet_vehicle_state(id) ON DELETE SET NULL;
ALTER TABLE "fleet_vehicle" ADD CONSTRAINT "fleet_vehicle_write_uid_fkey" FOREIGN KEY (write_uid) REFERENCES res_users(id) ON DELETE SET NULL;
ALTER TABLE "fleet_vehicle_odometer" ADD CONSTRAINT "fleet_vehicle_odometer_create_uid_fkey" FOREIGN KEY (create_uid) REFERENCES res_users(id) ON DELETE SET NULL;
ALTER TABLE "fleet_vehicle_odometer" ADD CONSTRAINT "fleet_vehicle_odometer_driver_id_fkey" FOREIGN KEY (driver_id) REFERENCES res_partner(id) ON DELETE SET NULL;
ALTER TABLE "fleet_vehicle_odometer" ADD CONSTRAINT "fleet_vehicle_odometer_service_id_fkey" FOREIGN KEY (service_id) REFERENCES fleet_vehicle_log_services(id) ON DELETE SET NULL;
ALTER TABLE "fleet_vehicle_odometer" ADD CONSTRAINT "fleet_vehicle_odometer_vehicle_id_fkey" FOREIGN KEY (vehicle_id) REFERENCES fleet_vehicle(id) ON DELETE RESTRICT;
ALTER TABLE "fleet_vehicle_odometer" ADD CONSTRAINT "fleet_vehicle_odometer_write_uid_fkey" FOREIGN KEY (write_uid) REFERENCES res_users(id) ON DELETE SET NULL;
ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_brand_id_fkey" FOREIGN KEY (brand_id) REFERENCES fleet_vehicle_model_brand(id) ON DELETE SET NULL;
ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_company_id_fkey" FOREIGN KEY (company_id) REFERENCES res_company(id) ON DELETE SET NULL;
ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_create_uid_fkey" FOREIGN KEY (create_uid) REFERENCES res_users(id) ON DELETE SET NULL;
ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_manager_id_fkey" FOREIGN KEY (manager_id) REFERENCES res_users(id) ON DELETE SET NULL;
ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_model_id_fkey" FOREIGN KEY (model_id) REFERENCES fleet_vehicle_model(id) ON DELETE SET NULL;
ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_odometer_id_fkey" FOREIGN KEY (odometer_id) REFERENCES fleet_vehicle_odometer(id) ON DELETE SET NULL;
ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_purchaser_id_fkey" FOREIGN KEY (purchaser_id) REFERENCES res_partner(id) ON DELETE SET NULL;
ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_service_type_id_fkey" FOREIGN KEY (service_type_id) REFERENCES fleet_service_type(id) ON DELETE RESTRICT;
ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_technician_id_fkey" FOREIGN KEY (technician_id) REFERENCES res_partner(id) ON DELETE SET NULL;
ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_vehicle_id_fkey" FOREIGN KEY (vehicle_id) REFERENCES fleet_vehicle(id) ON DELETE RESTRICT;
ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_vendor_id_fkey" FOREIGN KEY (vendor_id) REFERENCES res_partner(id) ON DELETE SET NULL;
ALTER TABLE "fleet_vehicle_log_services" ADD CONSTRAINT "fleet_vehicle_log_services_write_uid_fkey" FOREIGN KEY (write_uid) REFERENCES res_users(id) ON DELETE SET NULL;
ALTER TABLE "motorbike_battery" ADD CONSTRAINT "motorbike_battery_create_uid_fkey" FOREIGN KEY (create_uid) REFERENCES res_users(id) ON DELETE SET NULL;
ALTER TABLE "motorbike_battery" ADD CONSTRAINT "motorbike_battery_write_uid_fkey" FOREIGN KEY (write_uid) REFERENCES res_users(id) ON DELETE SET NULL;
ALTER TABLE "motorbike_battery_assignment" ADD CONSTRAINT "motorbike_battery_assignment_battery_id_fkey" FOREIGN KEY (battery_id) REFERENCES motorbike_battery(id) ON DELETE RESTRICT;
ALTER TABLE "motorbike_battery_assignment" ADD CONSTRAINT "motorbike_battery_assignment_create_uid_fkey" FOREIGN KEY (create_uid) REFERENCES res_users(id) ON DELETE SET NULL;
ALTER TABLE "motorbike_battery_assignment" ADD CONSTRAINT "motorbike_battery_assignment_vehicle_id_fkey" FOREIGN KEY (vehicle_id) REFERENCES fleet_vehicle(id) ON DELETE CASCADE;
ALTER TABLE "motorbike_battery_assignment" ADD CONSTRAINT "motorbike_battery_assignment_write_uid_fkey" FOREIGN KEY (write_uid) REFERENCES res_users(id) ON DELETE SET NULL;
ALTER TABLE "motorbike_maintenance_plan" ADD CONSTRAINT "motorbike_maintenance_plan_create_uid_fkey" FOREIGN KEY (create_uid) REFERENCES res_users(id) ON DELETE SET NULL;
ALTER TABLE "motorbike_maintenance_plan" ADD CONSTRAINT "motorbike_maintenance_plan_service_type_id_fkey" FOREIGN KEY (service_type_id) REFERENCES fleet_service_type(id) ON DELETE SET NULL;
ALTER TABLE "motorbike_maintenance_plan" ADD CONSTRAINT "motorbike_maintenance_plan_vehicle_id_fkey" FOREIGN KEY (vehicle_id) REFERENCES fleet_vehicle(id) ON DELETE CASCADE;
ALTER TABLE "motorbike_maintenance_plan" ADD CONSTRAINT "motorbike_maintenance_plan_write_uid_fkey" FOREIGN KEY (write_uid) REFERENCES res_users(id) ON DELETE SET NULL;

-- ADDITIONAL INDEXES (including one open battery assignment per vehicle/pin)
CREATE INDEX fleet_vehicle__vehicle_code_index ON fleet_vehicle USING btree (vehicle_code);
CREATE INDEX fleet_vehicle_log_services__vehicle_id_index ON fleet_vehicle_log_services USING btree (vehicle_id);
CREATE INDEX motorbike_battery__battery_code_index ON motorbike_battery USING btree (battery_code);
CREATE UNIQUE INDEX motorbike_assignment_open_battery ON motorbike_battery_assignment USING btree (battery_id) WHERE (removed_at IS NULL);
CREATE UNIQUE INDEX motorbike_assignment_open_vehicle ON motorbike_battery_assignment USING btree (vehicle_id) WHERE (removed_at IS NULL);

COMMIT;
