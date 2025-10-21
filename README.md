# MsSQL Sub Module Backend

## SELECT
EndPoin:
```
http://localhost:8000/api/querytool/read/
```
Body:
```
{
  "sql": "SELECT * FROM d_transaksi..t_schedule",
  "params": [],
  "server": "server1",
  "skip": 0,
  "take": 100
}
or
{
  "sql": "SELECT * FROM d_transaksi..t_schedule WHERE FC_SONO in ('FOP:25080454') AND FC_APPROVE = ?",
  "params": ["N"],
  "server": "server1",
  "skip": 0,
  "take": 50
}

```

## INSERT
EndPoin:
```
http://localhost:8000/api/querytool/create/
```
Body:
```
{
  "sql": "INSERT INTO d_transaksi..t_schedule (FC_SONO, FC_APPROVE, FD_DATE) VALUES ('FOP:25080454', 'Y', '2025-10-01')",
  "params": [],
  "server": "server1"
}
or
{
  "sql": "INSERT INTO d_transaksi..t_schedule (FC_SONO, FC_APPROVE, FD_DATE) VALUES (?, ?, ?)",
  "params": ["FOP:25080454", "N", "2025-10-20"],
  "server": "server1"
}
```

## UPDATE
EndPoin:
```
http://localhost:8000/api/querytool/update/
```
Body:
```
{
  "sql": "UPDATE d_transaksi..t_schedule SET FC_APPROVE = 'Y' WHERE FC_SONO = 'FOP:25080454'",
  "params": [],
  "server": "server1",
  "skip": 0,
  "take": 100
}
or
{
  "sql": "UPDATE d_transaksi..t_schedule SET FC_APPROVE = ? WHERE FC_SONO = ?",
  "params": ["Y", "FOP:25080454"],
  "server": "server1"
}
```

## DELETE
EndPoin:
```
http://localhost:8000/api/querytool/delete/
```
Body:
```
{
  "sql": "DELETE FROM d_transaksi..t_schedule WHERE FC_SONO='FOP:25080454'",
  "params": [],
  "server": "server1",
  "skip": 0,
  "take": 100
}
or
{
  "sql": "DELETE FROM d_transaksi..t_schedule WHERE FC_SONO = ?",
  "params": ["FOP:25080454"],
  "server": "server1"
}
```


