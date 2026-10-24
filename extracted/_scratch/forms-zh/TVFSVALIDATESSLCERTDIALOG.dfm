object VfsValidateSSLCertDialog: TVfsValidateSSLCertDialog
  Caption = 'Enter Password'
  ClientHeight = 265
  ClientWidth = 409
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object Image: TUiImage
    Left = 16
    Top = 16
    Width = 32
    Height = 32
    Picture.Data = {TPngImage 7647 bytes}
    Stretch = True
    Transparent = True
  end
  object Lbl: TUiLabel
    Left = 64
    Top = 16
    Width = 337
    Height = 39
    Caption = 'Information you exchange with this site cannot be viewed or changed by others.  However, there is a problem with the site''s security certificate.'
    WordWrap = True
  end
  object CertAuthorityImage: TUiImage
    Left = 64
    Top = 65
    Width = 16
    Height = 16
    Images = BcImages.MainImages
  end
  object CertAuthorityLbl: TUiLabel
    Left = 88
    Top = 65
    Width = 313
    Height = 13
    Caption = '%'
    WordWrap = True
  end
  object DateImage: TUiImage
    Left = 64
    Top = 106
    Width = 16
    Height = 16
    Images = BcImages.MainImages
  end
  object DateLbl: TUiLabel
    Left = 88
    Top = 106
    Width = 313
    Height = 13
    Caption = '%'
    WordWrap = True
  end
  object CommonNameImage: TUiImage
    Left = 64
    Top = 147
    Width = 16
    Height = 16
    Images = BcImages.MainImages
  end
  object CommonNameLbl: TUiLabel
    Left = 88
    Top = 147
    Width = 313
    Height = 13
    Caption = '%'
    WordWrap = True
  end
  object AddToCacheLbl: TUiLabel
    Left = 64
    Top = 188
    Height = 13
    Caption = 'Trust this host and continue connecting?'
  end
  object AddToCacheEdit: TUiCheckBox
    Left = 64
    Top = 209
    Height = 17
    Caption = '&Always trust certificate in future sessions'
    TabOrder = 0
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 226
    Width = 409
    TabOrder = 1
    object OkBtn: TUiOkBtn
      Caption = '&Connect'
    end
    object CancelBtn: TUiCancelBtn
    end
    object ViewCertificateBtn: TUiAdvancedBtn
      Caption = '&View Certificate'
      OnClick = ViewCertificateClick
    end
  end
end
