FROM postgres:16 AS postgres-libpq

FROM odoo:18.0

USER root
COPY --from=postgres-libpq /usr/lib/x86_64-linux-gnu/libpq.so.5.18 /usr/lib/x86_64-linux-gnu/libpq.so.5.18
RUN ln -sf libpq.so.5.18 /usr/lib/x86_64-linux-gnu/libpq.so.5 \
    && test -s /usr/lib/x86_64-linux-gnu/libpq.so.5.18 \
    && id odoo

USER odoo
