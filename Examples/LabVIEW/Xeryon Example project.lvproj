<?xml version='1.0' encoding='UTF-8'?>
<Project Type="Project" LVVersion="14008000">
	<Item Name="My Computer" Type="My Computer">
		<Property Name="IOScan.Faults" Type="Str"></Property>
		<Property Name="IOScan.NetVarPeriod" Type="UInt">100</Property>
		<Property Name="IOScan.NetWatchdogEnabled" Type="Bool">false</Property>
		<Property Name="IOScan.Period" Type="UInt">10000</Property>
		<Property Name="IOScan.PowerupMode" Type="UInt">0</Property>
		<Property Name="IOScan.Priority" Type="UInt">9</Property>
		<Property Name="IOScan.ReportModeConflict" Type="Bool">true</Property>
		<Property Name="IOScan.StartEngineOnDeploy" Type="Bool">false</Property>
		<Property Name="NI.SortType" Type="Int">3</Property>
		<Property Name="server.app.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="server.control.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="server.tcp.enabled" Type="Bool">false</Property>
		<Property Name="server.tcp.port" Type="Int">0</Property>
		<Property Name="server.tcp.serviceName" Type="Str">My Computer/VI Server</Property>
		<Property Name="server.tcp.serviceName.default" Type="Str">My Computer/VI Server</Property>
		<Property Name="server.vi.callsEnabled" Type="Bool">true</Property>
		<Property Name="server.vi.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="specify.custom.address" Type="Bool">false</Property>
		<Item Name="Static single axis example.vi" Type="VI" URL="../Static single axis example.vi"/>
		<Item Name="Static dual axis example.vi" Type="VI" URL="../Static dual axis example.vi"/>
		<Item Name="Dynamic multi axis example.vi" Type="VI" URL="../Dynamic multi axis example.vi"/>
		<Item Name="Dependencies" Type="Dependencies">
			<Item Name="vi.lib" Type="Folder">
				<Item Name="DialogType.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/DialogType.ctl"/>
				<Item Name="Clear Errors.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Clear Errors.vi"/>
				<Item Name="subTimeDelay.vi" Type="VI" URL="/&lt;vilib&gt;/express/express execution control/TimeDelayBlock.llb/subTimeDelay.vi"/>
				<Item Name="VISA Configure Serial Port" Type="VI" URL="/&lt;vilib&gt;/Instr/_visa.llb/VISA Configure Serial Port"/>
				<Item Name="VISA Configure Serial Port (Instr).vi" Type="VI" URL="/&lt;vilib&gt;/Instr/_visa.llb/VISA Configure Serial Port (Instr).vi"/>
				<Item Name="VISA Configure Serial Port (Serial Instr).vi" Type="VI" URL="/&lt;vilib&gt;/Instr/_visa.llb/VISA Configure Serial Port (Serial Instr).vi"/>
				<Item Name="Trim Whitespace.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Trim Whitespace.vi"/>
				<Item Name="whitespace.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/whitespace.ctl"/>
				<Item Name="Simple Error Handler.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Simple Error Handler.vi"/>
				<Item Name="General Error Handler.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/General Error Handler.vi"/>
				<Item Name="DialogTypeEnum.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/DialogTypeEnum.ctl"/>
				<Item Name="General Error Handler Core CORE.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/General Error Handler Core CORE.vi"/>
				<Item Name="Check Special Tags.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Check Special Tags.vi"/>
				<Item Name="TagReturnType.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/TagReturnType.ctl"/>
				<Item Name="Set String Value.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Set String Value.vi"/>
				<Item Name="GetRTHostConnectedProp.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/GetRTHostConnectedProp.vi"/>
				<Item Name="Error Code Database.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Error Code Database.vi"/>
				<Item Name="Format Message String.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Format Message String.vi"/>
				<Item Name="Find Tag.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Find Tag.vi"/>
				<Item Name="Search and Replace Pattern.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Search and Replace Pattern.vi"/>
				<Item Name="Set Bold Text.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Set Bold Text.vi"/>
				<Item Name="Details Display Dialog.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Details Display Dialog.vi"/>
				<Item Name="ErrWarn.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/ErrWarn.ctl"/>
				<Item Name="eventvkey.ctl" Type="VI" URL="/&lt;vilib&gt;/event_ctls.llb/eventvkey.ctl"/>
				<Item Name="Not Found Dialog.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Not Found Dialog.vi"/>
				<Item Name="Three Button Dialog.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Three Button Dialog.vi"/>
				<Item Name="Three Button Dialog CORE.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Three Button Dialog CORE.vi"/>
				<Item Name="LVRectTypeDef.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/miscctls.llb/LVRectTypeDef.ctl"/>
				<Item Name="Longest Line Length in Pixels.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Longest Line Length in Pixels.vi"/>
				<Item Name="Convert property node font to graphics font.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Convert property node font to graphics font.vi"/>
				<Item Name="Get Text Rect.vi" Type="VI" URL="/&lt;vilib&gt;/picture/picture.llb/Get Text Rect.vi"/>
				<Item Name="Get String Text Bounds.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Get String Text Bounds.vi"/>
				<Item Name="LVBoundsTypeDef.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/miscctls.llb/LVBoundsTypeDef.ctl"/>
				<Item Name="BuildHelpPath.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/BuildHelpPath.vi"/>
				<Item Name="GetHelpDir.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/GetHelpDir.vi"/>
				<Item Name="Application Directory.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/file.llb/Application Directory.vi"/>
				<Item Name="NI_FileType.lvlib" Type="Library" URL="/&lt;vilib&gt;/Utility/lvfile.llb/NI_FileType.lvlib"/>
				<Item Name="Error Cluster From Error Code.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Error Cluster From Error Code.vi"/>
			</Item>
			<Item Name="Xeryon serial driver.vi" Type="VI" URL="../Serial driver/Xeryon serial driver.vi"/>
			<Item Name="Xeryon serial data buffer.vi" Type="VI" URL="../Serial driver/Xeryon serial data buffer.vi"/>
			<Item Name="Serial parameters.ctl" Type="VI" URL="../Serial driver/Serial parameters.ctl"/>
			<Item Name="Xeryon status bits.ctl" Type="VI" URL="../Axis driver/Xeryon status bits.ctl"/>
			<Item Name="Xeryon Arange Parameters.vi" Type="VI" URL="../Axis driver/Xeryon Arange Parameters.vi"/>
			<Item Name="Add stage type info.vi" Type="VI" URL="../Axis driver/Add stage type info.vi"/>
			<Item Name="Xeryon convert stage type.vi" Type="VI" URL="../Axis driver/Xeryon convert stage type.vi"/>
			<Item Name="Xeryon build statusbits array.vi" Type="VI" URL="../Axis driver/Xeryon build statusbits array.vi"/>
			<Item Name="Xeryon convert statusbits.vi" Type="VI" URL="../Axis driver/Xeryon convert statusbits.vi"/>
			<Item Name="Process serial data.vi" Type="VI" URL="../Serial driver/Process serial data.vi"/>
			<Item Name="Xeryon send serial data.vi" Type="VI" URL="../Serial driver/Xeryon send serial data.vi"/>
			<Item Name="Axis config.ctl" Type="VI" URL="../Axis Manager/Axis config.ctl"/>
			<Item Name="Read config file.vi" Type="VI" URL="../Axis Manager/Read config file.vi"/>
			<Item Name="Axis ref manager.vi" Type="VI" URL="../Axis driver/Axis ref manager.vi"/>
			<Item Name="Sequencer.vi" Type="VI" URL="../Sequencer/Sequencer.vi"/>
			<Item Name="Sequencer mode.ctl" Type="VI" URL="../Sequencer/Sequencer mode.ctl"/>
			<Item Name="Xeryon add drive letter.vi" Type="VI" URL="../Axis driver/Xeryon add drive letter.vi"/>
			<Item Name="Xeryon unit conversion.vi" Type="VI" URL="../Axis driver/Xeryon unit conversion.vi"/>
			<Item Name="Xeryon Axis driver.vi" Type="VI" URL="../Axis driver/Xeryon Axis driver.vi"/>
			<Item Name="Xeryon process command.vi" Type="VI" URL="../Axis driver/Xeryon process command.vi"/>
			<Item Name="Xeryon filter commands.vi" Type="VI" URL="../Axis driver/Xeryon filter commands.vi"/>
			<Item Name="Xeryon Read COM port number.vi" Type="VI" URL="../Serial driver/Xeryon Read COM port number.vi"/>
			<Item Name="Xeryon Enter COM Port number.vi" Type="VI" URL="../Serial driver/Xeryon Enter COM Port number.vi"/>
			<Item Name="Axis Manager.vi" Type="VI" URL="../Axis Manager/Axis Manager.vi"/>
			<Item Name="Remove driveletter on 1 axis system.vi" Type="VI" URL="../Axis Manager/Remove driveletter on 1 axis system.vi"/>
			<Item Name="Axis enum.ctl" Type="VI" URL="../Axis Manager/Axis enum.ctl"/>
			<Item Name="Drive type properties.vi" Type="VI" URL="../Axis Manager/Drive type properties.vi"/>
			<Item Name="Overzicht axes.vi" Type="VI" URL="../Axis Manager/Overzicht axes.vi"/>
			<Item Name="Xeryon Axis command.ctl" Type="VI" URL="../Axis driver/Xeryon Axis command.ctl"/>
			<Item Name="Xeryon Axis receive command.vi" Type="VI" URL="../Axis driver/Xeryon Axis receive command.vi"/>
			<Item Name="Xeryon serial command.ctl" Type="VI" URL="../Serial driver/Xeryon serial command.ctl"/>
			<Item Name="Xeryon serial SendCommand.vi" Type="VI" URL="../Serial driver/Xeryon serial SendCommand.vi"/>
			<Item Name="Xeryon Axis SendCommand.vi" Type="VI" URL="../Axis driver/Xeryon Axis SendCommand.vi"/>
			<Item Name="Xeryon SetDPos command.vi" Type="VI" URL="../Axis driver/Xeryon SetDPos command.vi"/>
			<Item Name="Xeryon serial receive command.vi" Type="VI" URL="../Serial driver/Xeryon serial receive command.vi"/>
		</Item>
		<Item Name="Build Specifications" Type="Build">
			<Item Name="Static single axis" Type="EXE">
				<Property Name="App_copyErrors" Type="Bool">true</Property>
				<Property Name="App_INI_aliasGUID" Type="Str">{D296E4B1-F743-4D0B-BE8A-595E4BD99876}</Property>
				<Property Name="App_INI_GUID" Type="Str">{46DD492E-EE45-4352-BC63-4063AEAEC38B}</Property>
				<Property Name="App_serverConfig.httpPort" Type="Int">8002</Property>
				<Property Name="Bld_autoIncrement" Type="Bool">true</Property>
				<Property Name="Bld_buildCacheID" Type="Str">{40DF0CB0-B56C-496A-B5A9-319A602D826C}</Property>
				<Property Name="Bld_buildSpecName" Type="Str">Static single axis</Property>
				<Property Name="Bld_excludeInlineSubVIs" Type="Bool">true</Property>
				<Property Name="Bld_excludeLibraryItems" Type="Bool">true</Property>
				<Property Name="Bld_excludePolymorphicVIs" Type="Bool">true</Property>
				<Property Name="Bld_localDestDir" Type="Path">../Executable</Property>
				<Property Name="Bld_localDestDirType" Type="Str">relativeToCommon</Property>
				<Property Name="Bld_modifyLibraryFile" Type="Bool">true</Property>
				<Property Name="Bld_previewCacheID" Type="Str">{9400960A-CAA0-4B9E-8199-6136112B118D}</Property>
				<Property Name="Bld_version.major" Type="Int">1</Property>
				<Property Name="Destination[0].destName" Type="Str">Xeryon single axis.exe</Property>
				<Property Name="Destination[0].path" Type="Path">../Executable/Xeryon single axis.exe</Property>
				<Property Name="Destination[0].preserveHierarchy" Type="Bool">true</Property>
				<Property Name="Destination[0].type" Type="Str">App</Property>
				<Property Name="Destination[1].destName" Type="Str">Support Directory</Property>
				<Property Name="Destination[1].path" Type="Path">../Executable/data</Property>
				<Property Name="DestinationCount" Type="Int">2</Property>
				<Property Name="Source[0].itemID" Type="Str">{73A3754F-5B1B-4C63-984E-903EC53D1A3B}</Property>
				<Property Name="Source[0].type" Type="Str">Container</Property>
				<Property Name="Source[1].destinationIndex" Type="Int">0</Property>
				<Property Name="Source[1].itemID" Type="Ref">/My Computer/Static single axis example.vi</Property>
				<Property Name="Source[1].sourceInclusion" Type="Str">TopLevel</Property>
				<Property Name="Source[1].type" Type="Str">VI</Property>
				<Property Name="SourceCount" Type="Int">2</Property>
				<Property Name="TgtF_companyName" Type="Str">Ninix Technologies</Property>
				<Property Name="TgtF_fileDescription" Type="Str">Static single axis</Property>
				<Property Name="TgtF_internalName" Type="Str">Static single axis</Property>
				<Property Name="TgtF_legalCopyright" Type="Str">Copyright © 2024 Ninix Technologies</Property>
				<Property Name="TgtF_productName" Type="Str">Static single axis</Property>
				<Property Name="TgtF_targetfileGUID" Type="Str">{CDDE8DFE-6936-470D-B448-1FDFAB38B9A4}</Property>
				<Property Name="TgtF_targetfileName" Type="Str">Xeryon single axis.exe</Property>
			</Item>
			<Item Name="Static dual axis" Type="EXE">
				<Property Name="App_copyErrors" Type="Bool">true</Property>
				<Property Name="App_INI_aliasGUID" Type="Str">{F9FC8372-1004-415B-9A79-C36D3BE05E1F}</Property>
				<Property Name="App_INI_GUID" Type="Str">{06668A49-936C-4A7C-B514-761E78BD544D}</Property>
				<Property Name="App_serverConfig.httpPort" Type="Int">8002</Property>
				<Property Name="Bld_autoIncrement" Type="Bool">true</Property>
				<Property Name="Bld_buildCacheID" Type="Str">{2B6B6F96-3876-4B6B-9903-D00E2341EC5F}</Property>
				<Property Name="Bld_buildSpecName" Type="Str">Static dual axis</Property>
				<Property Name="Bld_excludeInlineSubVIs" Type="Bool">true</Property>
				<Property Name="Bld_excludeLibraryItems" Type="Bool">true</Property>
				<Property Name="Bld_excludePolymorphicVIs" Type="Bool">true</Property>
				<Property Name="Bld_localDestDir" Type="Path">../Executable</Property>
				<Property Name="Bld_localDestDirType" Type="Str">relativeToCommon</Property>
				<Property Name="Bld_modifyLibraryFile" Type="Bool">true</Property>
				<Property Name="Bld_previewCacheID" Type="Str">{4D5928B4-6D3A-4ADE-8EA3-8F2EB5925E9A}</Property>
				<Property Name="Bld_version.major" Type="Int">1</Property>
				<Property Name="Destination[0].destName" Type="Str">Xeryon dual axis.exe</Property>
				<Property Name="Destination[0].path" Type="Path">../Executable/Xeryon dual axis.exe</Property>
				<Property Name="Destination[0].preserveHierarchy" Type="Bool">true</Property>
				<Property Name="Destination[0].type" Type="Str">App</Property>
				<Property Name="Destination[1].destName" Type="Str">Support Directory</Property>
				<Property Name="Destination[1].path" Type="Path">../Executable/data</Property>
				<Property Name="DestinationCount" Type="Int">2</Property>
				<Property Name="Source[0].itemID" Type="Str">{73A3754F-5B1B-4C63-984E-903EC53D1A3B}</Property>
				<Property Name="Source[0].type" Type="Str">Container</Property>
				<Property Name="Source[1].destinationIndex" Type="Int">0</Property>
				<Property Name="Source[1].itemID" Type="Ref">/My Computer/Static single axis example.vi</Property>
				<Property Name="Source[1].type" Type="Str">VI</Property>
				<Property Name="Source[2].destinationIndex" Type="Int">0</Property>
				<Property Name="Source[2].itemID" Type="Ref">/My Computer/Static dual axis example.vi</Property>
				<Property Name="Source[2].sourceInclusion" Type="Str">TopLevel</Property>
				<Property Name="Source[2].type" Type="Str">VI</Property>
				<Property Name="SourceCount" Type="Int">3</Property>
				<Property Name="TgtF_companyName" Type="Str">Ninix Technologies</Property>
				<Property Name="TgtF_fileDescription" Type="Str">Static single axis</Property>
				<Property Name="TgtF_internalName" Type="Str">Static single axis</Property>
				<Property Name="TgtF_legalCopyright" Type="Str">Copyright © 2024 Ninix Technologies</Property>
				<Property Name="TgtF_productName" Type="Str">Static single axis</Property>
				<Property Name="TgtF_targetfileGUID" Type="Str">{39BAE196-9F2B-48C4-9435-0A7CB03D43C5}</Property>
				<Property Name="TgtF_targetfileName" Type="Str">Xeryon dual axis.exe</Property>
			</Item>
			<Item Name="Dynamic multi axis" Type="EXE">
				<Property Name="App_copyErrors" Type="Bool">true</Property>
				<Property Name="App_INI_aliasGUID" Type="Str">{0A74BE59-BF85-4BF7-9502-4893784061FB}</Property>
				<Property Name="App_INI_GUID" Type="Str">{C4472576-A4F0-4514-9253-9B46B22D7E02}</Property>
				<Property Name="App_serverConfig.httpPort" Type="Int">8002</Property>
				<Property Name="Bld_autoIncrement" Type="Bool">true</Property>
				<Property Name="Bld_buildCacheID" Type="Str">{BC1D71A6-96E1-4AA9-BD37-1BBD55A2D4D1}</Property>
				<Property Name="Bld_buildSpecName" Type="Str">Dynamic multi axis</Property>
				<Property Name="Bld_excludeInlineSubVIs" Type="Bool">true</Property>
				<Property Name="Bld_excludeLibraryItems" Type="Bool">true</Property>
				<Property Name="Bld_excludePolymorphicVIs" Type="Bool">true</Property>
				<Property Name="Bld_localDestDir" Type="Path">../Executable</Property>
				<Property Name="Bld_localDestDirType" Type="Str">relativeToCommon</Property>
				<Property Name="Bld_modifyLibraryFile" Type="Bool">true</Property>
				<Property Name="Bld_previewCacheID" Type="Str">{4BD40117-46EF-46E5-90AB-2B26098063DA}</Property>
				<Property Name="Bld_version.major" Type="Int">1</Property>
				<Property Name="Destination[0].destName" Type="Str">Xeryon dynamic multi axes.exe</Property>
				<Property Name="Destination[0].path" Type="Path">../Executable/Xeryon dynamic multi axes.exe</Property>
				<Property Name="Destination[0].preserveHierarchy" Type="Bool">true</Property>
				<Property Name="Destination[0].type" Type="Str">App</Property>
				<Property Name="Destination[1].destName" Type="Str">Support Directory</Property>
				<Property Name="Destination[1].path" Type="Path">../Executable/data</Property>
				<Property Name="DestinationCount" Type="Int">2</Property>
				<Property Name="Source[0].itemID" Type="Str">{73A3754F-5B1B-4C63-984E-903EC53D1A3B}</Property>
				<Property Name="Source[0].type" Type="Str">Container</Property>
				<Property Name="Source[1].destinationIndex" Type="Int">0</Property>
				<Property Name="Source[1].itemID" Type="Ref">/My Computer/Static single axis example.vi</Property>
				<Property Name="Source[1].type" Type="Str">VI</Property>
				<Property Name="Source[2].destinationIndex" Type="Int">0</Property>
				<Property Name="Source[2].itemID" Type="Ref">/My Computer/Static dual axis example.vi</Property>
				<Property Name="Source[2].type" Type="Str">VI</Property>
				<Property Name="Source[3].destinationIndex" Type="Int">0</Property>
				<Property Name="Source[3].itemID" Type="Ref">/My Computer/Dynamic multi axis example.vi</Property>
				<Property Name="Source[3].sourceInclusion" Type="Str">TopLevel</Property>
				<Property Name="Source[3].type" Type="Str">VI</Property>
				<Property Name="SourceCount" Type="Int">4</Property>
				<Property Name="TgtF_companyName" Type="Str">Ninix Technologies</Property>
				<Property Name="TgtF_fileDescription" Type="Str">Static single axis</Property>
				<Property Name="TgtF_internalName" Type="Str">Static single axis</Property>
				<Property Name="TgtF_legalCopyright" Type="Str">Copyright © 2024 Ninix Technologies</Property>
				<Property Name="TgtF_productName" Type="Str">Static single axis</Property>
				<Property Name="TgtF_targetfileGUID" Type="Str">{E060C35F-946B-4E62-BAB6-154AAB283971}</Property>
				<Property Name="TgtF_targetfileName" Type="Str">Xeryon dynamic multi axes.exe</Property>
			</Item>
		</Item>
	</Item>
</Project>
