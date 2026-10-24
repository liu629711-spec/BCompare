object VfsViewSSLCertDialog: TVfsViewSSLCertDialog
  Caption = 'View Certificate'
  ClientHeight = 517
  ClientWidth = 409
  PixelsPerInch = 96
  TextHeight = 13
  object SubjectLbl: TUiLabel
    Left = 8
    Top = 8
    Height = 13
    Caption = 'Subject'
    FontStyle = [fsBold]
  end
  object SubjectCommonNameDescLbl: TUiLabel
    Left = 8
    Top = 29
    Height = 13
    Caption = 'Common name:'
  end
  object SubjectCommonNameLbl: TUiLabel
    Left = 120
    Top = 29
    Height = 13
    Caption = '%'
  end
  object SubjectOrganizationDescLbl: TUiLabel
    Left = 8
    Top = 50
    Height = 13
    Caption = 'Organization:'
  end
  object SubjectOrganizationLbl: TUiLabel
    Left = 120
    Top = 50
    Height = 13
    Caption = '%'
  end
  object SubjectOriganizationalUnitDescLbl: TUiLabel
    Left = 8
    Top = 71
    Height = 13
    Caption = 'Unit:'
  end
  object SubjectOriganizationalUnitLbl: TUiLabel
    Left = 120
    Top = 71
    Height = 13
    Caption = '%'
  end
  object SubjectCountryDescLbl: TUiLabel
    Left = 8
    Top = 92
    Height = 13
    Caption = 'Country:'
  end
  object SubjectCountryLbl: TUiLabel
    Left = 120
    Top = 92
    Height = 13
    Caption = '%'
  end
  object SubjectStateDescLbl: TUiLabel
    Left = 8
    Top = 113
    Height = 13
    Caption = 'State:'
  end
  object SubjectStateLbl: TUiLabel
    Left = 120
    Top = 113
    Height = 13
    Caption = '%'
  end
  object SubjectLocalityDescLbl: TUiLabel
    Left = 8
    Top = 134
    Height = 13
    Caption = 'Locality:'
  end
  object SubjectLocalityLbl: TUiLabel
    Left = 120
    Top = 134
    Height = 13
    Caption = '%'
  end
  object SubjectEmailDescLbl: TUiLabel
    Left = 8
    Top = 155
    Height = 13
    Caption = 'Email:'
  end
  object SubjectEmailLbl: TUiLabel
    Left = 120
    Top = 155
    Height = 13
    Caption = '%'
  end
  object IssuerBevel: TUiBevel
    Left = 8
    Top = 176
    Width = 393
    Height = 1
    Shape = bsTopLine
  end
  object IssuerLbl: TUiLabel
    Left = 8
    Top = 184
    Height = 13
    Caption = 'Issuer'
    FontStyle = [fsBold]
  end
  object IssuerCommonNameDescLbl: TUiLabel
    Left = 8
    Top = 205
    Height = 13
    Caption = 'Common name:'
  end
  object IssuerCommonNameLbl: TUiLabel
    Left = 120
    Top = 205
    Height = 13
    Caption = '%'
  end
  object IssuerOrganizationDescLbl: TUiLabel
    Left = 8
    Top = 226
    Height = 13
    Caption = 'Organization:'
  end
  object IssuerOrganizationLbl: TUiLabel
    Left = 120
    Top = 226
    Height = 13
    Caption = '%'
  end
  object IssuerOrganizationalUnitDescLbl: TUiLabel
    Left = 8
    Top = 247
    Height = 13
    Caption = 'Unit:'
  end
  object IssuerOrganizationalUnitLbl: TUiLabel
    Left = 120
    Top = 247
    Height = 13
    Caption = '%'
  end
  object IssuerCountryDescLbl: TUiLabel
    Left = 8
    Top = 268
    Height = 13
    Caption = 'Country:'
  end
  object IssuerCountryLbl: TUiLabel
    Left = 120
    Top = 268
    Height = 13
    Caption = '%'
  end
  object IssuerStateDescLbl: TUiLabel
    Left = 8
    Top = 289
    Height = 13
    Caption = 'State:'
  end
  object IssuerStateLbl: TUiLabel
    Left = 120
    Top = 289
    Height = 13
    Caption = '%'
  end
  object IssuerLocalityDescLbl: TUiLabel
    Left = 8
    Top = 310
    Height = 13
    Caption = 'Locality:'
  end
  object IssuerLocalityLbl: TUiLabel
    Left = 120
    Top = 310
    Height = 13
    Caption = '%'
  end
  object IssuerEmailDescLbl: TUiLabel
    Left = 8
    Top = 331
    Height = 13
    Caption = 'Email:'
  end
  object IssuerEmailLbl: TUiLabel
    Left = 120
    Top = 331
    Height = 13
    Caption = '%'
  end
  object DetailsBevel: TUiBevel
    Left = 8
    Top = 352
    Width = 393
    Height = 1
    Shape = bsTopLine
  end
  object DetailsLbl: TUiLabel
    Left = 8
    Top = 360
    Height = 13
    Caption = 'Details'
    FontStyle = [fsBold]
  end
  object IssuedOnDescLbl: TUiLabel
    Left = 8
    Top = 381
    Height = 13
    Caption = 'Issued on:'
  end
  object IssuedOnLbl: TUiLabel
    Left = 120
    Top = 381
    Height = 13
    Caption = '%'
  end
  object ExpiresOnDescLbl: TUiLabel
    Left = 8
    Top = 402
    Height = 13
    Caption = 'Expires on:'
  end
  object ExpiresOnLbl: TUiLabel
    Left = 120
    Top = 402
    Height = 13
    Caption = '%'
  end
  object SerialNumberDescLbl: TUiLabel
    Left = 8
    Top = 423
    Height = 13
    Caption = 'Serial number:'
  end
  object SerialNumberLbl: TUiLabel
    Left = 120
    Top = 423
    Height = 13
    Caption = '%'
  end
  object MD5FingerprintDescLbl: TUiLabel
    Left = 8
    Top = 444
    Height = 13
    Caption = 'MD5 fingerprint:'
  end
  object MD5FingerprintLbl: TUiLabel
    Left = 120
    Top = 444
    Height = 13
    Caption = '%'
  end
  object SHA1FingerprintDescLbl: TUiLabel
    Left = 8
    Top = 465
    Height = 13
    Caption = 'SHA1 fingerprint:'
  end
  object SHA1FingerprintLbl: TUiLabel
    Left = 120
    Top = 465
    Height = 13
    Caption = '%'
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 478
    Width = 409
    TabOrder = 0
    object CloseBtn: TUiCloseBtn
    end
  end
end
